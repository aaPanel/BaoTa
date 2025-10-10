#coding: utf-8
import json
import os.path
import re
from typing import Union, Optional, List, Tuple

import public
import hashlib
import pwd
from .common import LimitNet, Redirect
try:
    import idna
except:
    public.ExecShell('btpip install idna')
    import idna


class projectBase(LimitNet, Redirect):

    def check_port(self, port):
        '''
        @name  检查端口是否被占用
        @args port:端口号
        @return: 被占用返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        a = public.ExecShell("netstat -nltp|awk '{print $4}'")
        if a[0]:
            if re.search(':' + port + '\n', a[0]):
                return True
            else:
                return False
        else:
            return False

    def is_domain(self, domain):
        '''
        @name 验证域名合法性
        @args domain:域名
        @return: 合法返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        import re
        domain_regex = re.compile(r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z', re.IGNORECASE)
        return True if domain_regex.match(domain) else False


    def generate_random_port(self):
        '''
        @name 生成随机端口
        @args
        @return: 端口号
        @author: lkq 2021-08-28
        '''
        import random
        port = str(random.randint(5000, 10000))
        while True:
            if not self.check_port(port): break
            port = str(random.randint(5000, 10000))
        return port

    def IsOpen(self, port):
        '''
        @name 检查端口是否被占用
        @args port:端口号
        @return: 被占用返回True，否则返回False
        @author: lkq 2021-08-28
        '''
        ip = '0.0.0.0'
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect((ip, int(port)))
            s.shutdown(2)
            return True
        except:
            return False

    # 判断域名是否有效，并返回
    def check_domain(self, domain: str) -> Union[str, bool]:
        domain = self.domain_to_puny_code(domain)
        # 判断通配符域名格式
        if domain.find('*') != -1 and domain.find('*.') == -1:
            return False

        # 判断域名格式
        reg = "^([\w\-\*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$"
        if not re.match(reg, domain):
            return False
        return domain

    def advance_check_port(self, get):
        """预先检查端口是否合格
        @author baozi <202-02-22>
        @param:
            port  ( str ):  端口号
        @return
        """
        port = getattr(get, "port", "")
        try:
            port = int(port)
            if 0 < port < 65535:
                data = public.ExecShell("ss  -nultp|grep ':%s '" % port)[0]
                if data:
                    msg = public.returnMsg(False, "请注意：该端口已经被占用")
                else:
                    msg = public.returnMsg(True, "验证成功")
            else:
                msg = public.returnMsg(False, "请输入正确的端口范围 1 < 端口 < 65535")
        except ValueError:
            msg = public.returnMsg(False, "请注意：该端口号为整数")

        return msg

    @staticmethod
    def get_system_user_list(get=None):
        """
        默认只返回uid>= 1000 的用户 和 root
        get中包含 sys_user 返回 uid>= 100 的用户 和 root
        get中包含 all_user 返回所有的用户
        """
        sys_user = False
        all_user = False
        if get is not None:
            if hasattr(get, "sys_user"):
                sys_user = True
            if hasattr(get, "all_user"):
                all_user = True

        user_set = set()
        try:
            for tmp_uer in pwd.getpwall():
                if tmp_uer.pw_uid == 0:
                    user_set.add(tmp_uer.pw_name)
                elif tmp_uer.pw_uid >= 1000:
                    user_set.add(tmp_uer.pw_name)
                elif sys_user and tmp_uer.pw_uid >= 100:
                    user_set.add(tmp_uer.pw_name)
                elif all_user:
                    user_set.add(tmp_uer.pw_name)
        except Exception:
            pass
        return list(user_set)

    @staticmethod
    def _pass_dir_for_user(path_dir: str, user: str):
        """
        给某个用户，对应目录的执行权限
        """
        import stat
        if not os.path.isdir(path_dir):
            return
        try:
            import pwd
            uid_data = pwd.getpwnam(user)
            uid = uid_data.pw_uid
            gid = uid_data.pw_gid
        except:
            return

        if uid == 0:
            return

        if path_dir[:-1] == "/":
            path_dir = path_dir[:-1]

        while path_dir != "/":
            path_dir_stat = os.stat(path_dir)
            if path_dir_stat.st_uid != uid or path_dir_stat.st_gid != gid:
                old_mod = stat.S_IMODE(path_dir_stat.st_mode)
                if not old_mod & 1:
                    os.chmod(path_dir, old_mod+1)
            path_dir = os.path.dirname(path_dir)

    @staticmethod
    def _check_webserver():
        setup_path = public.GetConfigValue('setup_path')
        ng_path = setup_path + '/nginx/sbin/nginx'
        ap_path = setup_path + '/apache/bin/apachectl'
        op_path = '/usr/local/lsws/bin/lswsctrl'
        not_server = False
        if not os.path.exists(ng_path) and not os.path.exists(ap_path) and not os.path.exists(op_path):
            not_server = True
        if not not_server:
            return
        tasks = public.M('tasks').where("status!=? AND type!=?", ('1','download')).field('id,name').select()
        for task in tasks:
            name = task["name"].lower()
            if name.find("openlitespeed") != -1:
                return "正在安装OpenLiteSpeed服务，请等待安装完成后再操作"
            if name.find("nginx") != -1:
                return "正在安装Nginx服务，请等待安装完成后再操作"
            if name.lower().find("apache") != -1:
                return "正在安装Apache服务，请等待安装完成后再操作"

        return "未安装任意Web服务，请安装Nginx或Apache后再操作"

    def _release_firewall(self, get):
        """尝试放行端口
        @author baozi <202-04-18>
        @param:
            get  ( dict_obj ):  创建项目的请求
        @return
        """

        from safeModel.firewallModel import main as firewall

        release = getattr(get, "release_firewall", None)
        if release in ("0", '', None, False, 0):
            return False, "注意：端口未在防火墙放行，仅可本地访问"
        port = getattr(get, "port", None)
        project_name = getattr(get, "name", "") or getattr(get, "pjname", "") or getattr(get, "project_name", "")
        if port is None:
            return True, ""

        new_get = public.dict_obj()
        new_get.protocol = "tcp"
        new_get.ports = str(port)
        new_get.choose = "all"
        new_get.address = ""
        new_get.domain = ""
        new_get.types = "accept"
        new_get.brief = "网站项目：" + project_name + "放行的端口"
        new_get.source = ""
        try:
            firewall_obj = firewall()
            get_obj = public.dict_obj()
            get_obj.p = 1
            get_obj.limit = 99
            get_obj.query = str(port)
            res_data = firewall_obj.get_rules_list(get_obj)  # 查询是否已经有端口

            if len(res_data) == 0:
                res = firewall_obj.create_rules(new_get)
            for i in res_data:
                new_get.id = i.get("id")
                res = firewall_obj.modify_rules(new_get)

            if res["status"]:
                return True, ""
            else:
                return False, "注意：端口在防火墙放行操作失败，仅可本地访问"
        except:
            return False, "注意：端口在防火墙放行操作失败，仅可本地访问"

    @staticmethod
    def stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = True
        public.writeFile(file_path, json.dumps(data))

    @staticmethod
    def start_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        data[str(project_id)] = False
        public.writeFile(file_path, json.dumps(data))

    @staticmethod
    def is_stop_by_user(project_id):
        file_path = "{}/data/push/tips/project_stop.json".format(public.get_panel_path())
        if not os.path.exists(file_path):
            data = {}
        else:
            data_content = public.readFile(file_path)
            try:
                data = json.loads(data_content)
            except json.JSONDecodeError:
                data = {}
        if str(project_id) not in data:
            return False
        return data[str(project_id)]

    def is_nginx_http3(self):
        """判断nginx是否可以使用http3"""
        if getattr(self, "_is_nginx_http3", None) is None:
            _is_nginx_http3 = public.ExecShell("nginx -V 2>&1| grep 'http_v3_module'")[0] != ''
            setattr(self, "_is_nginx_http3", _is_nginx_http3)
        return self._is_nginx_http3

    def set_daemon_time(self, get):
        """设置守护进程重启检测时间"""
        try:
            daemon_time = int(get.daemon_time.strip())
        except (ValueError, AttributeError):
            return public.returnMsg(False, "参数错误")

        public.writeFile("/www/server/panel/data/daemon_time.pl", str(daemon_time))
        return public.returnMsg(True, "设置成功")

    def get_daemon_time(self, get):
        """获取守护进程重启检测时间"""
        res = public.readFile("/www/server/panel/data/daemon_time.pl")
        if res is False:
            return {
                "status": True,
                "daemon_time": 120
            }
        return {
                "status": True,
                "daemon_time": int(res)
            }

    def _project_mod_type(self) -> Optional[str]:
        mod_name = self.__class__.__module__

        # "projectModel/javaModel.py" 的格式
        if "/" in mod_name:
            mod_name = mod_name.rsplit("/", 1)[1]
        if mod_name.endswith(".py"):
            mod_name = mod_name[:-3]

        # "projectModel.javaModel" 的格式
        if "." in mod_name:
            mod_name = mod_name.rsplit(".", 1)[1]

        if mod_name.endswith("Model"):
            return mod_name[:-5]
        return mod_name

    def project_site_types(self, get=None):
        p_type = self._project_mod_type()
        res = _ProjectSiteType().list_by_type(p_type)
        res_data = [
            {"id": 0, "name": "默认分类", "ps": ""},
        ] + res
        return res_data

    def add_project_site_type(self, get):
        try:
            type_name = get.type_name.strip()
            ps = get.ps.strip()
        except AttributeError:
            return public.returnMsg(False, "参数错误")

        if len(type_name) > 16:
            return public.returnMsg(False, "名称过长，请不要超出16位")

        p_type = self._project_mod_type()

        flag, msg = _ProjectSiteType().add(p_type, type_name, ps)
        if not flag:
            return public.returnMsg(False, msg)
        return public.returnMsg(True, "添加成功")

    def modify_project_site_type(self, get):
        try:
            type_name = get.type_name.strip()
            ps = get.ps.strip()
            type_id = int(get.type_id.strip())
        except (AttributeError, ValueError, TypeError):
            return public.returnMsg(False, "参数错误")

        if len(type_name) > 16:
            return public.returnMsg(False, "名称过长，请不要超出16位")

        p_type = self._project_mod_type()
        flag = _ProjectSiteType().modify(p_type, type_id, type_name, ps)
        if not flag:
            return public.returnMsg(False, "修改错误")
        return public.returnMsg(True, "修改成功")

    def remove_project_site_type(self, get):
        try:
            type_id = int(get.type_id.strip())
        except (AttributeError, ValueError, TypeError):
            return public.returnMsg(False, "参数错误")

        p_type = self._project_mod_type()

        project_type_map = {
            "go": "Go",
            "java": "Java",
            "net": "net",
            "nodejs": "Node",
            "other": "Other",
            "python": "Python",
            "proxy": "proxy",
            "html": "html",
        }
        if p_type not in project_type_map:
            return public.returnMsg(False, "参数错误")

        flag = _ProjectSiteType().remove(p_type, type_id)
        if not flag:
            return public.returnMsg(False, "删除错误")

        p_t = project_type_map[p_type]
        query_str = 'project_type=? AND type_id=?'
        projects = public.M('sites').where(query_str, (p_t, type_id)).field("id").select()
        if not projects:
            return public.returnMsg(True, "删除成功")

        project_ids = [i["id"] for i in projects]

        update_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(project_ids)))
        public.M('sites').where(update_str, (p_t, *project_ids)).update({"type_id": 0})

        return public.returnMsg(True, "删除成功")

    def find_project_site_type(self, type_id: int):
        if isinstance(type_id, str):
            try:
                type_id = int(type_id)
            except (AttributeError, ValueError, TypeError):
                return None
        if type_id == 0:
            return {
                "id": 0,
                "name": "默认分类",
                "ps": ""
            }
        p_type = self._project_mod_type()
        return _ProjectSiteType().find(p_type, type_id)

    def set_project_site_type(self, get):
        try:
            type_id = int(get.type_id.strip())
            if isinstance(get.site_ids, str):
                site_ids = json.loads(get.site_ids.strip())
            else:
                site_ids = get.site_ids
        except (AttributeError, ValueError, TypeError):
            return public.returnMsg(False, "参数错误")

        if not isinstance(site_ids, list):
            return public.returnMsg(False, "参数错误")

        p_type = self._project_mod_type()
        project_type_map = {
            "go": "Go",
            "java": "Java",
            "net": "net",
            "nodejs": "Node",
            "other": "Other",
            "python": "Python",
            "proxy": "proxy",
            "html": "html",
        }
        if p_type not in project_type_map:
            return public.returnMsg(False, "参数错误")

        if not self.find_project_site_type(type_id):
            return public.returnMsg(False, "没有指定的分类id")

        p_t = project_type_map[p_type]
        query_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(site_ids)))
        projects = public.M('sites').where(query_str, (p_t, *site_ids)).field("id").select()
        if not projects:
            return public.returnMsg(False, "未选中要启动的站点")

        project_ids = [i["id"] for i in projects]

        update_str = 'project_type=? AND id in ({})'.format(",".join(["?"] * len(project_ids)))
        public.M('sites').where(update_str, (p_t, *project_ids)).update({"type_id": type_id})

        return public.returnMsg(True, "设置成功")

    # 域名编码转换
    @staticmethod
    def domain_to_puny_code(domain):
        match = re.search(u"[^u\0000-u\001f]+", domain)
        if not match:
            return domain
        try:
            if domain.startswith("*."):
                return "*." + idna.encode(domain[2:]).decode("utf8")
            else:
                return idna.encode(domain).decode("utf8")
        except:
            return domain

    @staticmethod
    def del_user_ini_file(path, sub_path_limit=0):
        def real_remove(base_path, sub_limit: int):
            if not os.path.isdir(base_path):
                return

            user_ini_file = base_path + '/.user.ini'
            if os.path.exists(user_ini_file):
                public.ExecShell('chattr -i ' + user_ini_file)
                try:
                    os.remove(user_ini_file)
                except:
                    pass

            if sub_limit <= 0:
                return

            for p in os.listdir(path):
                sub_path = path + '/' + p
                if not os.path.isdir(sub_path):
                    continue
                real_remove(sub_path, sub_limit - 1)

        real_remove(path, sub_path_limit)

    @staticmethod
    def apache_add_ports(port: str = None, port_list: List[str] = None):
        if not port and not port_list:
            return

        all_prot = set()
        if port:
            all_prot.add(port)
        if port_list:
            all_prot |= set(port_list)

        filename = '/www/server/apache/conf/extra/httpd-ssl.conf'
        if os.path.isfile(filename):
            ssl_conf = public.readFile(filename)
            if isinstance(ssl_conf, str) and ssl_conf.find('Listen 443') != -1:
                ssl_conf = ssl_conf.replace('Listen 443', '')
                public.writeFile(filename, ssl_conf)

        filename = '/www/server/apache/conf/httpd.conf'
        if not os.path.isfile(filename):
            return
        ap_conf = public.readFile(filename)
        if not isinstance(ap_conf, str):
            return
        rep_ports = re.compile(r"Listen\s+(?P<port>[0-9]+)\n", re.M)
        last_idx = None
        for key in rep_ports.finditer(ap_conf):
            last_idx = key.end()
            if key.group("port") in all_prot:
                all_prot.remove(key.group("port"))

        if not last_idx:
            return
        new_conf = ap_conf[:last_idx] + "\n".join(["Listen %s" % i for i in all_prot]) + "\n" + ap_conf[last_idx:]
        public.writeFile(filename, new_conf)
        return True

    @staticmethod
    def _get_sites_log_path():
        log_path = public.readFile("{}/data/sites_log_path.pl".format(public.get_panel_path()))
        if isinstance(log_path, str) and os.path.isdir(log_path):
            return log_path
        return public.GetConfigValue('logs_path')

    @staticmethod
    def _nginx_set_domain(project_id, project_name, prefix="") -> bool:
        file = '/www/server/panel/vhost/nginx/{}{}.conf'.format(prefix, project_name)
        conf = public.readFile(file)
        if not conf:
            return False
        all_domains_data = public.M('domain').where('pid=?', (project_id,)).select()
        if not isinstance(all_domains_data, list):
            return False
        domains, ports = set(), set()
        for i in all_domains_data:
            domains.add(i["name"])
            ports.add(str(i["port"]))

        # 设置域名
        rep_server_name = re.compile(r"\s*server_name\s*(.*);", re.M)
        new_conf = rep_server_name.sub("\n    server_name {};".format(" ".join(domains)), conf, 1)

        # 设置端口
        rep_port = re.compile(r"\s*listen\s+[\[\]:]*(?P<port>[0-9]+).*;[^\n]*\n", re.M)
        listen_ipv6 = public.listen_ipv6()
        last_port_idx = None
        need_remove_port_idx = []
        had_ports = set()
        for tmp_res in rep_port.finditer(new_conf):
            last_port_idx = tmp_res.end()
            if tmp_res.group("port") in ports:
                had_ports.add(tmp_res.group("port"))
            elif tmp_res.group("port") != "443":
                need_remove_port_idx.append((tmp_res.start(), tmp_res.end()))

        if not last_port_idx:
            return False

        ports = ports - had_ports
        if ports:
            listen_add_list = []
            for p in ports:
                tmp = "    listen {};\n".format(p)
                if listen_ipv6:
                    tmp += "    listen [::]:{};\n".format(p)
                listen_add_list.append(tmp)

            new_conf = new_conf[:last_port_idx] + "".join(listen_add_list) + new_conf[last_port_idx:]

        # 移除多余的port监听：
        # 所有遍历的索引都在 last_port_idx 之前，所有不会影响之前的修改 ↑
        if need_remove_port_idx:
            conf_list = []
            idx = 0
            for start, end in need_remove_port_idx:
                conf_list.append(new_conf[idx:start])
                idx = end
            conf_list.append(new_conf[idx:])
            new_conf = "".join(conf_list)

        # 保存配置文件
        public.writeFile(file, new_conf)
        return True


class ProcessTask:
    _cache_path = "{}/data/process_cache.json".format(public.get_panel_path())

    def __init__(self, model: str, func: str, args: dict, ignore_check: bool = False):
        self.task_id = hashlib.md5((model + func + json.dumps(args)).encode()).hexdigest()
        self.model = model
        self.func = func
        self.args = args
        if ignore_check:
            self._remove_cache()

    def _check_exists(self) -> bool:
        if os.path.exists(self._cache_path):
            try:
                data: list = json.loads(public.readFile(self._cache_path))
            except:
                data = []
            if self.task_id not in data:
                data.append(self.task_id)
                public.writeFile(self._cache_path, json.dumps(data))
                return False
            else:
                return True
        data = [self.task_id, ]
        public.writeFile(self._cache_path, json.dumps(data))
        return False

    def _remove_cache(self) -> None:
        if os.path.exists(self._cache_path):
            data: list = json.loads(public.readFile(self._cache_path))
            if self.task_id in data:
                data.remove(self.task_id)
                public.writeFile(self._cache_path, json.dumps(data))

    def _run(self) -> None:
        from importlib import import_module
        module = import_module(".{}".format(self.model), package="projectModel")
        main_class = getattr(module, "main", None)
        if main_class:
            func = getattr(main_class(), self.func, None)
            if func is not None and callable(func):
                func(self.args)
                self._remove_cache()

    def run(self) -> Union[bool, int]:
        from multiprocessing import Process
        if self._check_exists():
            return False
        p = Process(target=self._run)
        p.start()
        return p.pid


class _ProjectSiteType:
    _CONFIG_FILE = "{}/config/project_site.json".format(public.get_panel_path())
    allow_type = {"go", "java", "net", "nodejs", "other", "python", "proxy", "html"}

    def __init__(self):
        self._config = None

    @classmethod
    def read_conf_file(cls):
        default_conf = {
            "go": {},
            "java": {},
            "net": {},
            "nodejs": {},
            "other": {},
            "python": {},
            "proxy": {},
            "html": {},
        }

        if not os.path.isfile(cls._CONFIG_FILE):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf

        conf_data = public.readFile(cls._CONFIG_FILE)
        if not isinstance(conf_data, str):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf

        try:
            conf = json.loads(conf_data)
        except json.JSONDecodeError:
            conf = None
        if not isinstance(conf, dict):
            public.writeFile(cls._CONFIG_FILE, json.dumps(default_conf))
            return default_conf
        return conf

    @property
    def config(self):
        if self._config is not None:
            return self._config
        self._config = self.read_conf_file()
        return self._config

    def save_config_to_file(self):
        if self._config:
            public.writeFile(self._CONFIG_FILE, json.dumps(self._config))

    def get_next_id(self, p_type: str) -> int:
        all_ids = [i["id"] for i in self.config[p_type].values()]
        return max(all_ids + [0]) + 1

    def add(self, p_type: str, name: str, ps: str) -> Tuple[bool, str]:
        if p_type not in self.allow_type:
            return False, "不允许的网站类型"

        if p_type not in self.config:
            self.config[p_type] = {}

        for t_info in self.config[p_type].values():
            if t_info["name"] == name:
                return False, "该名称已存在"

        next_id = self.get_next_id(p_type)
        self.config[p_type][str(next_id)] = {
            "id": next_id,
            "name": name,
            "ps": ps
        }
        self.save_config_to_file()
        return True, ""

    def modify(self, p_type: str, t_id: int, name: str, ps: str) -> bool:
        if p_type not in self.config:
            return False

        if str(t_id) not in self.config[p_type]:
            return False

        self.config[p_type][str(t_id)] = {
            "id": t_id,
            "name": name,
            "ps": ps
        }
        self.save_config_to_file()
        return True

    def remove(self, p_type: str, t_id: int) -> bool:
        if p_type not in self.config:
            return False

        if str(t_id) not in self.config[p_type]:
            return False

        del self.config[p_type][str(t_id)]

        self.save_config_to_file()
        return True

    def find(self, p_type: str, t_id: int) -> Optional[dict]:
        if p_type not in self.config:
            return None

        if str(t_id) not in self.config[p_type]:
            return None

        return self.config[p_type][str(t_id)]

    def list_by_type(self, p_type: str) -> List[dict]:
        if p_type not in self.config:
            return []
        return [i for i in self.config[p_type].values()]
