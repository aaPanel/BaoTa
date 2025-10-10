# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2017 宝塔软件(http:#bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: zhwen<zhw@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 站点目录密码保护
# ------------------------------
import public
import re
import os
import json
import shutil
import hashlib
import pwd
from base64 import b64encode
from typing import List, Dict, Tuple, Any


def _apr1_md5_crypt(password: str):
    # 将密码加密为标准的 apache 验证的 md5 格式
    salt = os.urandom(8).hex()[:8].lower()
    # 步骤1：初始哈希
    intermediate = hashlib.md5(password.encode('utf-8')).digest()
    intermediate = hashlib.md5(f"{password}{salt}".encode('utf-8')).digest()
    intermediate = hashlib.md5(intermediate + password.encode('utf-8')).digest()

    # 步骤2：迭代混合
    alt = (password + salt).encode('utf-8')
    for i in range(len(password)):
        intermediate = hashlib.md5(intermediate + alt).digest()

    # 步骤3：最终哈希
    temp = b""
    for _ in range(1000):
        ctx = hashlib.md5()
        if _ % 2 == 0:
            ctx.update(intermediate)
        else:
            ctx.update(alt)
        if _ % 3 != 0:
            ctx.update(salt.encode('utf-8'))
        if _ % 7 != 0:
            ctx.update(password.encode('utf-8'))
        temp = ctx.digest()
        intermediate = temp

    # 步骤4：Base64编码转换
    hash_bytes = intermediate
    apr1_hash = (
        b64encode(hash_bytes, altchars=b"./")
        .decode('utf-8')
        .replace('+', '.')
        .replace('=', '')[:22]
    )

    return f"$apr1${salt}${apr1_hash}"

def _base_crypt(password: str):
    # 将密码加密为简单的crypt
    return public.hasPwd(password)


class _SiteDirAuth:
    # 取目录加密状态
    def __init__(self):
        self.setup_path = public.GetConfigValue('setup_path')
        self.conf_file = self.setup_path + "/panel/data/site_dir_auth.json"
        # 配置文件格式实例
        # {
        #     "cache.cache.com": [  # 网站名称
        #         {
        #             "name": "sdvfs", # 名称
        #             "site_dir": "/",  # 目录
        #             "auth_file": "/www/server/pass/cache.cache.com/sdvfs.pass" # 密码文件路径
        #         }
        #     ]
        # }

    crypt_func = staticmethod(_base_crypt)

    # 读取配置
    def _read_conf(self) -> Dict[str, List[Dict[str,str]]]:
        conf = public.readFile(self.conf_file)
        if not conf:
            conf = {}
            public.writeFile(self.conf_file, json.dumps(conf))
            return conf
        try:
            conf = json.loads(conf)
            if not isinstance(conf, dict):
                conf = {}
                public.writeFile(self.conf_file, json.dumps(conf))
        except:
            conf = {}
            public.writeFile(self.conf_file, json.dumps(conf))
        return conf

    def _write_conf(self, conf, site_name):
        c = self._read_conf()
        if not c or site_name not in c:
            c[site_name] = [conf]
        else:
            if site_name in c:
                c[site_name].append(conf)
        public.writeFile(self.conf_file, json.dumps(c))

    def _check_site_authorization(self, site_name):
        webserver = public.get_webserver()
        conf_file = "{setup_path}/panel/vhost/{webserver}/{site_name}.conf".format(
            setup_path=self.setup_path, site_name=site_name, webserver=webserver)
        conf_content = public.readFile(conf_file)
        if re.search("auth_basic[^\n]+Authorization", conf_content):
            return True
        return False

    # 检查配置是否存在
    def _check_dir_auth(self, site_name, name, site_dir):
        conf = self._read_conf()
        if not conf:
            return False
        if site_name in conf:
            for i in conf[site_name]:
                if name == i["name"] or site_dir == i["site_dir"]:
                    return True

    # 获取当前站点php版本
    def get_site_php_version(self, siteName):
        try:
            conf = public.readFile(
                self.setup_path + '/panel/vhost/' + public.get_webserver() + '/' + siteName + '.conf');
            if public.get_webserver() == 'nginx':
                rep = "enable-php-(\w{2,5})\.conf"
            else:
                rep = "php-cgi-(\w{2,5})\.sock"
            tmp = re.search(rep, conf).groups()
            if tmp:
                return tmp[0]
            else:
                return ""
        except:
            return public.returnMsg(False, 'SITE_PHPVERSION_ERR_A22')

    # 获取站点名
    def get_site_info(self, id):
        site_info = public.M('sites').where('id=?', (id,)).field('name,path').find()
        return {"site_name": site_info["name"], "site_path": site_info["path"]}

    def change_dir_auth_file_nginx_phpver(self, site_name, phpv, auth_name):
        file_path = "{setup_path}/panel/vhost/nginx/dir_auth/{site_name}/{auth_name}.conf".format(
            setup_path=self.setup_path, site_name=site_name, auth_name=auth_name)
        conf = public.readFile(file_path)
        if not conf:
            return False

        if phpv == 'other':
            php_conf = "include /www/server/panel/vhost/other_php/{}/enable-php-other.conf;".format(site_name)
        else:
            php_conf = 'include enable-php-{}.conf;'.format(phpv)

        rep = r"include\s+(enable-php-\w+|/www/server/panel/vhost/other_php/{}/enable-php-other)\.conf;".format(
            site_name)
        conf = re.sub(rep, php_conf, conf)

        public.writeFile(file_path, conf)

    # 设置独立认证文件
    def set_dir_auth_file(self, site_path, site_name, name, username, site_dir, auth_file):
        php_ver = self.get_site_php_version(site_name)
        php_conf = ""
        if php_ver:
            if php_ver == 'other':
                php_conf = "include /www/server/panel/vhost/other_php/{}/enable-php-{}.conf;".format(site_name, php_ver)
            else:
                php_conf = "include enable-php-{}.conf;".format(php_ver)

        for i in ["nginx", "apache"]:
            file_path = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}"
            if i == "nginx":
                # 设置nginx
                conf = '''location ~* ^%s* {
    #AUTH_START
    auth_basic "Authorization";
    auth_basic_user_file %s;
    %s
    #AUTH_END
}''' % (site_dir, auth_file, php_conf)
            else:
                # 设置apache
                conf = '''<Directory "{site_path}{site_dir}">
    #AUTH_START
    AuthType basic
    AuthName "Authorization "
    AuthUserFile {auth_file}
    Require user {username}
    #AUTH_END
    SetOutputFilter DEFLATE
    Options FollowSymLinks
    AllowOverride All
    #Require all granted
        DirectoryIndex index.php index.html index.htm default.php default.html default.htm
</Directory>'''.format(site_path=site_path, site_dir=site_dir, auth_file=auth_file, username=username,
                       site_name=site_name)
            conf_file = file_path.format(setup_path=self.setup_path, site_name=site_name, webserver=i)
            if not os.path.exists(conf_file):
                os.makedirs(conf_file)
            conf_file = conf_file + '/{}.conf'.format(name)
            public.writeFile(conf_file, conf)

    # 设置apache配置
    def set_conf(self, site_name, act):
        try:
            for i in ["nginx", "apache"]:
                dir_auth_file = "%s/panel/vhost/%s/dir_auth/%s/*.conf" % (self.setup_path, i, site_name,)
                file = self.setup_path + "/panel/vhost/{}/".format(i) + site_name + ".conf"
                if os.path.exists(file):
                    shutil.copyfile(file, '/tmp/{}_file_bk.conf'.format(i))

                if os.path.exists(file):
                    conf = public.readFile(file)
                    if i == "apache":
                        if act == "create":
                            rep = "IncludeOptional.*\/dir_auth\/.*conf(\n|.)+<\/VirtualHost>"
                            rep1 = "</VirtualHost>"
                            if not re.search(rep, conf):
                                conf = conf.replace(rep1,
                                                    "\n\t#Directory protection rules, do not manually delete\n\tIncludeOptional {}\n</VirtualHost>".format(
                                                        dir_auth_file))
                        else:
                            rep = "\n*#Directory protection rules, do not manually delete\n+\s+IncludeOptional[\s\w\/\.\*]+"
                            conf = re.sub(rep, '', conf)
                        public.writeFile(file, conf)
                    else:
                        if act == "create":
                            rep = "#SSL-END(\n|.)+include.*\/dir_auth\/.*conf;"
                            rep1 = "#SSL-END"
                            if not re.search(rep, conf):
                                conf = conf.replace(rep1,
                                                    rep1 + "\n\t#Directory protection rules, do not manually delete\n\tinclude {};".format(
                                                        dir_auth_file))
                        else:
                            rep = "\n*#Directory protection rules, do not manually delete\n+\s+include[\s\w\/\.\*]+;"
                            conf = re.sub(rep, '', conf)
                        public.writeFile(file, conf)
        except:
            pass

    # 验证站点配置
    def check_site_conf(self, webserver, site_name, name):
        isError = public.checkWebConfig()
        auth_file = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}/{name}.conf".format(
            setup_path=self.setup_path, webserver=webserver, site_name=site_name, name=name)
        if (isError != True):
            os.remove(auth_file)
            # a_conf = self._read_conf()
            # for i in range(len(a_conf)-1,-1,-1):
            #     if site_name == a_conf[i]["sitename"] and a_conf[i]["proxyname"]:
            #         del a_conf[i]
            return public.returnMsg(False, 'ERROR: %s<br><a style="color:red;">' % public.GetMsg(
                "CONFIG_ERROR") + isError.replace("\n",
                                                  '<br>') + '</a>')

    # 设置目录加密
    def set_dir_auth(self, get):
        '''
        get.name        auth_name
        get.site_dir         auth_dir
        get.username    username
        get.password    password
        get.id          site id
        :param get:
        :return:
        '''
        param = self.__check_param(get)
        if not param['status']:
            return param
        param = param['msg']
        password = param['password']
        username = param['username']
        name = param['name']
        site_dir = get.site_dir
        if public.get_webserver() == "openlitespeed":
            return public.returnMsg(False, "OpenLiteSpeed is currently not supported")
        if not get.site_dir:
            return public.returnMsg(False, '请输入需要保护的目录')
        if not get.name:
            return public.returnMsg(False, '请输入名称')
        passwd = self.crypt_func(password)
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        if self._check_site_authorization(site_name):
            return public.returnMsg(False, '已经设置站点密码保护，请取消后再设置 站点配置 --> 访问限制 --> 加密访问')
        if self._check_dir_auth(site_name, name, site_dir):
            return public.returnMsg(False, '此名称或目录已经存在！')
        # 与禁止访问做冲突建检查
        if not getattr(get, "force", False):
            flag, c_msg = self.check_contradiction(get.site_dir, site_name)
            if flag is None:
                return {'status': False, "tip": c_msg}
            if flag is False:
                return public.returnMsg(False, c_msg)
        auth = "{user}:{passwd}".format(user=username, passwd=passwd)
        auth_dir = '{setup_path}/pass/{site_name}'.format(setup_path=self.setup_path, site_name=site_name)
        if not os.path.exists(auth_dir):
            os.makedirs(auth_dir)
        auth_file = auth_dir + "/{}.pass".format(name)
        public.writeFile(auth_file, auth)
        self.set_pass_permissions(auth_dir)
        # 配置独立认证文件
        self.set_dir_auth_file(site_info["site_path"], site_name, name, username, site_dir, auth_file)
        # 配置站点主文件
        result = self.set_conf(site_name, "create")
        if result:
            return result
        # 检查配置
        webserver = public.get_webserver()
        result = self.check_site_conf(webserver, site_name, name)
        if result:
            return result
        # 写配置
        conf = {"name": name, "site_dir": get.site_dir, "auth_file": auth_file}
        self._write_conf(conf, site_name)
        public.serviceReload()
        return public.returnMsg(True, "创建成功")

    @staticmethod
    def set_pass_permissions(auth_dir: str):
        try:
            www = pwd.getpwnam("www")
            os.chown(auth_dir, www.pw_uid, www.pw_gid)
            os.chmod(auth_dir, 0o755)
            for i in os.listdir(auth_dir):
                if i.endswith(".pass"):
                    os.chmod(os.path.join(auth_dir, i), 0o644)
                    os.chown(auth_dir, www.pw_uid, www.pw_gid)
        except:
            pass


    # 删除密码保护
    def delete_dir_auth(self, get):
        '''
        get.id
        get.name
        :param get:
        :return:
        '''
        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        conf: Dict[str, List[Dict[str,str]]] = self._read_conf()
        if site_name not in conf:
            return public.returnMsg(False, "配置文件中不存在网站名：{}".format(site_name))
        target = None
        for item in conf[site_name]:
            if item["name"] == name:
                target = item
                break

        if target:
            conf[site_name].remove(target)
            if os.path.isfile(target["auth_file"]):
                os.remove(target["auth_file"])

        public.writeFile(self.conf_file, json.dumps(conf))
        for i in ["nginx", "apache"]:
            file_path = "{setup_path}/panel/vhost/{webserver}/dir_auth/{site_name}/{name}.conf".format(
                webserver=i,setup_path=self.setup_path,site_name=site_name,name=name)
            os.remove(file_path)
        if not conf:
            self.set_conf(site_name, "delete")

        if not hasattr(get, 'multiple'):
            public.serviceReload()

        if target and os.path.isfile(target["auth_file"]):
            os.remove(target["auth_file"])

        return public.returnMsg(True, "删除成功")

    # 修改目录保护密码
    def modify_dir_auth_pass(self, get):
        '''
        get.id
        get.name
        get.username
        get.password
        :param get:
        :return:
        '''
        param = self.__check_param(get)
        if not param['status']:
            return param
        param = param['msg']
        password = param['password']
        username = param['username']
        name = get.name
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        passwd = self.crypt_func(password)
        auth = "{user}:{passwd}".format(user=username, passwd=passwd)
        auth_file = '{setup_path}/pass/{site_name}/{name}.pass'.format(setup_path=self.setup_path, site_name=site_name,
                                                                       name=name)
        public.writeFile(auth_file, auth)
        public.serviceReload()
        return public.returnMsg(True, "修改成功")

    # 获取目录保护列表
    def get_dir_auth(self, get):
        '''
        get.id
        get.sitename
        :param get:
        :return:
        '''
        try:
            if not hasattr(get, 'siteName'):
                site_info = self.get_site_info(get.id)
                site_name = site_info["site_name"]
            else:
                site_name = get.siteName
            conf = self._read_conf()
            if site_name in conf:
                return {site_name: conf[site_name]}
            return {}
        except :
            return {}

    def __check_param(self, get):
        values = {}
        if hasattr(get, "password"):
            if not get.password:
                return public.returnMsg(False, '请输入密码!')
            password = get.password.strip()
            if len(password) < 3:
                return public.returnMsg(False, '密码不能少于3位')
            elif len(password) > 8:
                return public.returnMsg(False, '密码不能大于8位，超过8位的部分无法验证')
            if re.search('\s', password):
                return public.returnMsg(False, '密码不能存在空格')
            values['password'] = password

        if hasattr(get, "username"):
            if not get.username:
                return public.returnMsg(False, '请输入用户!')
            username = get.username.strip()
            if len(username) < 3:
                return public.returnMsg(False, '账号不能少于3位')
            if re.search('\s', username):
                return public.returnMsg(False, '账号不能存在空格')
            values['username'] = username

        if hasattr(get, "name"):
            if not get.name:
                return public.returnMsg(False, '请输入名称!')
            name = get.name.strip()
            if len(name) < 3:
                return public.returnMsg(False, '名称不能少于3位')
            if re.search('\s', name):
                return public.returnMsg(False, '名称不能存在空格')
            if re.search('[\/\"\'\!@#$%^&*()+={}\[\]\:\;\?><,./]+', name):
                return public.returnMsg(False, '名称格式错误，请参考格式：aaa_bbb')
            values['name'] = name

        return public.returnMsg(True, values)

    def check_contradiction(self, path, site_name ):
        from panelSite import panelSite
        args = public.dict_obj()
        args.sitename = site_name
        proxy_list = panelSite().GetProxyList(args)  # type: list[dict]
        for proxy in proxy_list:
            if path.startswith(proxy['proxydir']):
                return False, "目录已被【反向代理】至其他站点，无法添加"

        from file_execute_deny import FileExecuteDeny
        args.website = site_name
        deny_config = FileExecuteDeny().get_file_deny(args)
        names = []
        for i in deny_config:
            if i["dir"].startswith(path):
                names.append(i["dir"])
        if bool(names):
            names_str = "，".join(names)
            return None, "目录【{}】将会覆盖【禁止访问】中【{}】的禁止访问效果，使之变为加密访问，是否继续添加？".format(path, names_str)
        return True, ''



class MultiUserSiteDirAuth(_SiteDirAuth):
    # 配置文件格式实例
    # {
    #     "cache.cache.com": [  # 网站名称
    #         {
    #             "name": "sdvfs", # 名称
    #             "site_dir": "/",  # 目录
    #             "auth_file": "/www/server/pass/cache.cache.com/sdvfs.pass" # 密码文件路径
    #         }
    #     ]
    # }

    crypt_func = staticmethod(_base_crypt)


    @staticmethod
    def _parse_auth_file(auth_file: str) -> List[Tuple[str, str]]:
        if not os.path.isfile(auth_file):
            return []
        user_list = []
        file_data = public.readFile(auth_file)
        if not isinstance(file_data, str):
            return []
        for line in file_data.split("\n"):
            if not line:
                continue
            try:
                user, passwd = line.split(":")
                user_list.append((user, passwd))
            except:
                pass
        return user_list


    @classmethod
    def _get_auth_file_user_list(cls, auth_file: str) -> List[str]:
        user_list = []
        for user, _ in cls._parse_auth_file(auth_file):
            user_list.append(user)
        return user_list


    @classmethod
    def _remove_auth_file_user(cls, auth_file: str, user: str) -> bool:
        if not os.path.isfile(auth_file):
            return True

        user_list: List[str] = []
        for tmp_user, passwd in cls._parse_auth_file(auth_file):
            if tmp_user == user:
                continue
            user_list.append("{}:{}".format(tmp_user, passwd))

        public.writeFile(auth_file, "\n".join(user_list) + "\n")
        return True

    @classmethod
    def _add_or_modify_auth_file_user(cls, auth_file: str, user: str, password: str) -> bool:
        passwd_crypt = cls.crypt_func(password)
        user_list: List[str] = ["{}:{}".format(user, passwd_crypt)]
        for tmp_user, passwd in cls._parse_auth_file(auth_file):
            if tmp_user == user:
                continue
            user_list.append("{}:{}".format(tmp_user, passwd))


        public.writeFile(auth_file, "\n".join(user_list) + "\n")
        cls.set_pass_permissions(os.path.dirname(auth_file))
        return True

    def __check_param(self, get):
        values = {}
        option_args = get.get("option", "")
        if option_args == "remove":
            values['password'] = ""
        elif hasattr(get, "password"):
            if not get.password:
                return public.returnMsg(False, '请输入密码!')
            password = get.password.strip()
            if len(password) < 3:
                return public.returnMsg(False, '密码不能少于3位')
            elif len(password) > 8 and self.crypt_func is _base_crypt:
                return public.returnMsg(False, '密码不能大于8位，超过8位的部分无法验证')
            if re.search('\s', password):
                return public.returnMsg(False, '密码不能存在空格')
            values['password'] = password
        else:
            return public.returnMsg(False, '请输入密码!')

        if hasattr(get, "username") and get.username:
            username = get.username.strip()
            if len(username) < 3:
                return public.returnMsg(False, '账号不能少于3位')
            if re.search('\s', username):
                return public.returnMsg(False, '账号不能存在空格')
            values['username'] = username
        else:
            return public.returnMsg(False, '请输入用户!')

        if hasattr(get, "name") and get.name:
            name = get.name.strip()
            if len(name) < 3:
                return public.returnMsg(False, '名称不能少于3位')
            if re.search('[/\"\'!@#$%^&*()+={}\[\]:;?><,.\s]+', name):
                return public.returnMsg(False, '名称格式错误，请参考格式：aaa_bbb,且名称不能存在空格')
            values['name'] = name
        else:
            return public.returnMsg(False, '请输入名称!')

        return public.returnMsg(True, values)

    # 修改目录保护密码
    def modify_dir_auth_pass(self, get):
        '''
        get.id
        get.name
        get.username
        get.password
        :param get:
        :return:
        '''
        param = self.__check_param(get)
        if not param['status']:
            return param
        param = param['msg']
        password = param['password']
        username = param['username']
        name = get.get("name/s", "")
        site_id = get.get("id/d", 0)
        option = get.get("option/s", "add")
        if not name:
            return public.returnMsg(False, "请选择要修改的限制的名称")
        if not site_id:
            return public.returnMsg(False, "请选择要修改密码的站点")
        if option not in ("add", "remove"):
            return public.returnMsg(False, "操作类型的参数错误")
        site_info = self.get_site_info(get.id)
        site_name = site_info["site_name"]
        auth_file = '{setup_path}/pass/{site_name}/{name}.pass'.format(
            setup_path=self.setup_path, site_name=site_name, name=name)
        if option == "remove":
            if len(self._get_auth_file_user_list(auth_file)) <= 1:
                return self.delete_dir_auth(get)
            self._remove_auth_file_user(auth_file, username)
        else:
            self._add_or_modify_auth_file_user(auth_file, username, password)
        public.serviceReload()
        return public.returnMsg(True, "修改成功")

    def get_dir_auth(self, get):
        '''
        get.id
        get.sitename
        :param get:
        :return:
        '''
        site_name = get.get("siteName/s", "")
        if not site_name:
            site_id = get.get("id/d", 0)
            if not site_id:
                return public.returnMsg(False, "请选择要操作的站点")
            site_info = self.get_site_info(site_id)
            site_name = site_info["site_name"]

        conf = self._read_conf()
        site_conf: List[Dict[str, Any]] = conf.get(site_name, [])
        for site_conf_item in site_conf:
            if os.path.isfile(site_conf_item["auth_file"]):
                site_conf_item["user_list"] = self._get_auth_file_user_list(site_conf_item["auth_file"])
        return { site_name: site_conf }

SiteDirAuth = MultiUserSiteDirAuth