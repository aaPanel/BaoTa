# 格式化为符合面板要求的站点配置
import copy
import json
import os
import re
import shutil
import subprocess
import time
import ipaddress
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any, Union, Callable

from sqlalchemy.testing import exclude

from .. import Config, Server, Parser, Lexer, trans_, Location, Directive, Block, dump_config, Include, \
    Http, Upstream, dump_block, parse_file, IBlock, IDirective
from .site_detector import site_detector, SiteInfo, SITE_TYPE_STATIC, SITE_TYPE_PHP, SITE_TYPE_PROXY
from .nginx_detector import NginxInstance
from .panel_utils import panel_configs, panel_vhost_http_d_configs, panel_nginx_http_d_configs, panel_php_info_configs
from .rel2real_path import normalize_directive_paths


def _is_ip_domain(domain: str) -> bool:
    """
    判断域名是否是IP格式
    :param domain: 域名
    :return: 是否是IP格式
    """
    try:
        ipaddress.ip_address(domain)
        return True
    except ValueError:
        return False


def _parse_site_names(site_names: List[str]):
    ret_names = set()
    for domain in site_names:
        if ":"  not in domain:
            ret_names.add(domain)
            continue
        if domain.startswith("[") and domain.endswith("]"):
            if "]:" in domain:
                ret_names.add(domain.rsplit(":")[0])
            else:
                ret_names.add(domain)
        else:
            ret_names.add(domain.rsplit(":")[0])
    return list(ret_names)


@dataclass
class _StaticSite:
    """
    静态站点
    """
    name: str
    site_path: str
    site_names: List[str]
    ports: List[int]
    config: Config  # 站点配置
    other_configs: List[Config] = field(default_factory=list)

    def to_json(self):
        return {
            "name": self.name,
            "site_path": self.site_path,
            "site_names": self.site_names,
            "config_file": self.config.file_path,
            "site_type": "html",
            "ports": self.ports,
            "domains": _parse_site_names(self.site_names),
            "other_files": [i.file_path for i in self.other_configs],
        }

    @staticmethod
    def site_type():
        return "html"


@dataclass
class _PHPSite:
    """
    PHP站点
    """
    name: str
    site_path: str
    site_names: List[str]
    config: Config  # 站点配置
    php_sock: str
    ports: List[int]
    other_configs: List[Config] = field(default_factory=list)

    def to_json(self):
        return {
            "name": self.name,
            "site_path": self.site_path,
            "site_names": self.site_names,
            "config_file": self.config.file_path,
            "site_type": "PHP",
            "php_sock": self.php_sock,
            "ports": self.ports,
            "domains": _parse_site_names(self.site_names),
            "other_files": [i.file_path for i in self.other_configs],
        }

    @staticmethod
    def site_type():
        return "PHP"


@dataclass
class _ProxySite:
    """
    反向代理站点
    """
    name: str
    site_path: str
    site_names: List[str]
    config: Config  # 站点配置
    proxy_info: List[Dict[str, Any]]
    root_proxy: Dict[str, Any]
    ports: List[int]
    other_configs: List[Config] = field(default_factory=list)

    def to_json(self):
        return {
            "name": self.name,
            "site_path": self.site_path,
            "site_names": self.site_names,
            "config_file": self.config.file_path,
            "site_type": "proxy",
            "proxy_info": self.proxy_info,
            "root_proxy": self.root_proxy,
            "ports": self.ports,
            "domains": _parse_site_names(self.site_names),
            "other_files": [i.file_path for i in self.other_configs],
        }

    @staticmethod
    def site_type():
        return "proxy"


@dataclass
class NgOrgConf:
    """
    存储识别出来的官方配置文件 (
    fastcgi.conf  fastcgi_params koi-utf koi-win mimetypes.conf scgi_params uwsgi_params win-utf, proxy_params
    )
    """
    fastcgi_conf: Optional[Config] = None
    fastcgi_params: Optional[Config] = None
    koi_utf: Optional[Config] = None
    koi_win: Optional[Config] = None
    win_utf: Optional[Config] = None
    scgi_params: Optional[Config] = None
    uwsgi_params: Optional[Config] = None
    mimetypes_conf: Optional[Config] = None
    proxy_params: Optional[Config] = None

    def __contains__(self, item):
        attrs = (
            "fastcgi_conf", "fastcgi_params", "koi_utf", "koi_win",
            "win_utf", "scgi_params", "uwsgi_params", "mimetypes_conf","proxy_params"
        )

        for attr in attrs:
            if getattr(self, attr) and getattr(self, attr) == item:
                return True
        return False

    def __iter__(self):
        attrs = (
            "fastcgi_conf", "fastcgi_params", "koi_utf", "koi_win",
            "win_utf", "scgi_params", "uwsgi_params", "mimetypes_conf", "proxy_params",
        )
        for attr in attrs:
            if getattr(self, attr):
                yield getattr(self, attr)

    def __getitem__(self, item: str):
        if getattr(self, item):
            return getattr(self, item)

    @staticmethod
    def org_config_names():
        return {
            "fastcgi_conf": "fastcgi.conf",
            "fastcgi_params": "fastcgi_params",
            "koi_utf": "koi-utf",
            "koi_win": "koi-win",
            "win_utf": "win-utf",
            "scgi_params": "scgi_params",
            "uwsgi_params": "uwsgi_params",
            "mimetypes_conf": "mimetypes.conf",
            "proxy_params": "proxy_params",
        }


# 存放转化中的数据
@dataclass
class BtNginxConf:
    """
    面板要求的Nginx站点配置格式
    """
    tmp_conf_path: str  # 临时配置文件保存路径
    mian_conf: Config
    sites_conf: Dict[Tuple[str, ...], Union[_StaticSite, _PHPSite, _ProxySite]]
    default_server: Optional[_StaticSite]
    nginx_status_server: Optional[_StaticSite]
    include_files: Dict[str, Config]  # 存储所有server共用的配置文件
    bt_default_conf: Dict[str, Config]  # 存储面板默认配置文件
    http_conf_d: List[Config] = field(default_factory=list)  # 存储http段中引入的无server配置文件 /conf/config_http.d/**
    panel_http_conf_d: List[Config] = field(default_factory=list)  # 存储面板http段中引入的公共配置文件
    ng_org_conf: NgOrgConf = field(default_factory=NgOrgConf)
    todo_warning_list: List[str] = field(default_factory=list)

    def sites_show(self):
        print("==>站点列表<==")
        for site_name, site_info in self.sites_conf.items():
            print(f"+++++==>{site_name}<==+++++")
            print(f"  name: {site_info.name}")
            print(f"  site_path: {site_info.site_path}")
            print(f"  domains: {site_info.site_names}")

            if isinstance(site_info, _PHPSite):
                print(f"  php_sock:{site_info.php_sock}")
            elif isinstance(site_info, _ProxySite):
                print(f"  root_proxy:{site_info.root_proxy}")
                for proxy_info in site_info.proxy_info:
                    print(f"  proxy_info: {proxy_info}")

            print(f"  config_file: {site_info.config.file_path}")
            print(
                f"  conf_data:\n------------------------\n{dump_config(site_info.config)}\n------------------------\n\n")

    def show_main_conf(self):
        print("==>主配置文件<==")
        print(dump_config(self.mian_conf))

    def show_prep_files(self):
        print("======>所有配置文件<======")
        print(f"==>{self.mian_conf.file_path}<==")
        print(dump_config(self.mian_conf), "\n\n")
        for file_path, config in self.include_files.items():
            print(f"==>{config.file_path}<==")
            print(dump_config(config), "\n\n")
        for site in self.sites_conf.values():
            print(f"==>{site.config.file_path}<==")
            print(dump_config(site.config), "\n\n")
        for k, config in self.bt_default_conf.items():
            if config.file_path in self.include_files:
                continue
            print(f"==>{config.file_path}<==")
            print(dump_config(config), "\n\n")

        if self.default_server:
            print(f"==>{self.default_server.config.file_path}<==")
            print(dump_config(self.default_server.config), "\n\n")
        if self.nginx_status_server:
            print(f"==>{self.nginx_status_server.config.file_path}<==")
            print(dump_config(self.nginx_status_server.config), "\n\n")

    @staticmethod
    def _write_conf(config: Config):
        os.makedirs(os.path.dirname(config.file_path), exist_ok=True)
        with open(config.file_path, "w") as f:
            f.write(dump_config(config))

    def save_conf(self):
        site_conf_list = []
        other_files_map = {}

        def check_other_files_map(cf_file_path: str):
            for keyword in cf_file_path.split("/"):
                if keyword in other_files_map:
                    other_files_map[keyword].append(cf_file_path)
                    break

        self._write_conf(self.mian_conf)
        for site in self.sites_conf.values():
            self._write_conf(site.config)
            other_files_map[site.name] = []
            site_conf_list.append(site.to_json())
            for conf in site.other_configs:
                self._write_conf(conf)

        if self.ng_org_conf:
            for conf in self.ng_org_conf:
                conf.file_path = os.path.join(self.tmp_conf_path, "conf", os.path.basename(conf.file_path))
                self._write_conf(conf)

        for file_path, config in self.include_files.items():
            check_other_files_map(config.file_path)
            self._write_conf(config)

        for k, config in self.bt_default_conf.items():
            if config.file_path in self.include_files:
                continue
            self._write_conf(config)

        if self.default_server:
            self._write_conf(self.default_server.config)
        if self.nginx_status_server:
            self._write_conf(self.nginx_status_server.config)

        if self.panel_http_conf_d:
            for conf in self.panel_http_conf_d:
                self._write_conf(conf)

        if self.http_conf_d:
            for conf in self.http_conf_d:
                self._write_conf(conf)

        for site_c in site_conf_list:
            other_files = list(set(site_c["other_files"] + other_files_map.get(site_c["name"], [])))
            site_c["other_files"] = other_files

        with open(os.path.join(self.tmp_conf_path, "site_conf.json"), "w") as f:
            json.dump(site_conf_list, f)

    def test_nginx(self, nginx_bin_path: str = None ):
        """
        测试nginx配置文件
        :return:
        """
        nginx_bin = nginx_bin_path or "/www/server/nginx/sbin/nginx"

        vhost_path = "/www/server/panel/vhost"
        nginx_conf = "/www/server/nginx/conf"
        with _ConfileLink((self.tmp_conf_path + "/conf", nginx_conf), (self.tmp_conf_path + "/vhost", vhost_path)):
            cmd = [nginx_bin, "-t", "-p", os.path.dirname(nginx_conf),  "-c", "/www/server/nginx/conf/nginx.conf"]
            ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if ret.returncode != 0:
                print("nginx配置文件测试失败")
            else:
                print("nginx配置文件测试成功")
            print(ret.stdout.decode())
            print(ret.stderr.decode())


class ConfigParseError(ValueError):
    pass


class _Formatter:
    """
    格式化器
    """

    def __init__(self, nginx_instance: NginxInstance, tmp_conf_path: str = "./" ):
        """
        初始化格式化器
        :param nginx_instance: Nginx 实例
        """
        if not os.path.isdir(tmp_conf_path):
            os.makedirs(tmp_conf_path)
        tmp_conf_path = os.path.join(tmp_conf_path, "bt_nginx_format")
        if os.path.isdir(tmp_conf_path):
            shutil.rmtree(tmp_conf_path)

        os.makedirs(tmp_conf_path, exist_ok=True)
        self._tmp_path = tmp_conf_path
        self._tmp_conf_path = os.path.join(tmp_conf_path, "conf")
        self._tmp_sites_path = os.path.join(tmp_conf_path, "vhost/nginx")
        self._working_dir = nginx_instance.working_dir

        self.nginx_main_conf_file = nginx_instance.nginx_conf
        if not os.path.exists(nginx_instance.nginx_conf):
            raise FileNotFoundError(f"nginx main conf file not found: {nginx_instance.nginx_conf}")
        with open(nginx_instance.nginx_conf, "r") as f:
            config_content = f.read()

        already_site = panel_configs()

        def _skip_already_existing(include_path: str) -> bool:
            return include_path in already_site

        l = Lexer(config_content, nginx_instance.nginx_conf)
        self.parser = Parser(l, parse_include=True, main_config_path=nginx_instance.nginx_conf)
        self.parser.set_skip_include_func(_skip_already_existing)

        try:
            self.config = self.parser.parse()
        except ValueError as e:
            raise ConfigParseError(str(e))
        self.rel2real()  # 将相对路径转绝对路径
        warn_list = self.to_do_warning()
        self.config_includes = self.parser.parsed_includes
        self.ng_org_cfg = self._filter_nginx_org_config(self.config_includes)  # 被使用的官方配置文件
        self.try_get_other_nginx_conf() # 未被使用的官方配置文件，但可能或被面板默认存在的配置文件所解析，所以也需要引入
        self.panel_vhost_http_d_conf = panel_vhost_http_d_configs()
        self.panel_nginx_http_d_conf = panel_nginx_http_d_configs()
        self.panel_php_info_sock = panel_php_info_configs()

        self.bt_conf = BtNginxConf(
            tmp_conf_path=self._tmp_path,
            mian_conf=Config(
                directives=[],
                file_path=os.path.join(self._tmp_conf_path, "nginx.conf")
            ),  # 空的主配置文件，待后续填充
            sites_conf={},  # 站点配置，key为站点域名元组，value为SiteInfo
            default_server=None,
            nginx_status_server=None,
            include_files={},
            bt_default_conf={},
            http_conf_d=[],
            panel_http_conf_d=[],
            ng_org_conf=self.ng_org_cfg,
            todo_warning_list=warn_list,
        )

    # 从指令中查询会导致使用面板nginx异常的项目，并记录原因
    def to_do_warning(self) -> List[str]:
        res_list = set()
        # load_module
        def _check_load_module(directive: Directive):
            if directive.get_name() == "load_module":
                err_msg = "动态模块无法接管：{}".format(directive.get_parameters()[0])
                res_list.add(err_msg)

        # lua_package_path lua_package_cpath
        lua_msg = "第三方lua无法接管"
        def _check_lua_package_path(directive: Directive):
            if directive.get_name() in ("lua_package_path", "lua_package_cpath"):
                is_bt_waf = any([("btwaf" in i or "/www/server/nginx" in i) for i in directive.get_parameters()])
                if not is_bt_waf:
                    res_list.add(lua_msg)

        def _recursion(b):
            for d in b.directives:
                if d.__class__ is Include:  # include本身无需处理相对路径
                    inc = trans_(d, Include)
                    for sub_c in inc.configs:
                        _recursion(sub_c)
                else:
                    if hasattr(d, "parameters") and d.get_parameters():
                        for _c in (_check_load_module, _check_lua_package_path):
                            _c(d)
                sub_block = d.get_block()
                if sub_block:
                    _recursion(sub_block)

        _recursion(self.config)
        return list(res_list)


    # 指令中的相对路径转绝对路径
    def rel2real(self):
        nginx_conf_dir = os.path.dirname(self.nginx_main_conf_file)
        def _rel2real_block(b, env_dict: dict):# 待处理的配置块
            now_env_dict = copy.deepcopy(env_dict)
            if b.__class__ is Upstream:
                now_env_dict["upstream"] = True

            for d in b.directives:
                if d.__class__ is Include:  # include本身无需处理相对路径
                    inc = trans_(d, Include)
                    for sub_c in inc.configs:
                        _rel2real_block(sub_c, now_env_dict)
                else:
                    if hasattr(d, "parameters") and d.get_parameters():
                        normalize_directive_paths(d, prefix_path=self._working_dir, config_dir=nginx_conf_dir, block_env=now_env_dict)
                sub_block = d.get_block()
                if sub_block:
                    _rel2real_block(sub_block, now_env_dict)

        _rel2real_block(self.config, {})

    def to_bt_config(self) -> BtNginxConf:
        """
        格式化Nginx配置为面板要求的格式
        :return: 格式化后的Nginx配置
        """
        self._format_sites()  # 格式化站点配置
        self._format_default_server()  # 格式化默认站点配置
        self._build_main_other_conf()  # 构建主配置文件中和其他配置文件
        self._get_bt_default_conf()  # 获取面板默认配置
        self._set_main_bt_conf()
        self._replace_panel_http_conf()
        return self.bt_conf

    @staticmethod
    def _filter_no_server_includes(includes: Dict[str, Config]) -> Dict[str, Config]:
        ret_icd = {}
        for include_file, include_conf in includes.items():
            server = include_conf.find_directives("server", include=True, sub_block=False)
            if not any(type(s) is Server for s in server):  # 防止server 与 upstream 中的server 指令冲突
                ret_icd[include_file] = include_conf
        return ret_icd

    def _filter_nginx_org_config(self, includes: Dict[str, Config]) -> NgOrgConf:
        # 识别引用的官方配置文件 (
        # fastcgi.conf  fastcgi_params koi-utf koi-win mimetypes.conf scgi_params uwsgi_params win-utf
        # )
        ret = NgOrgConf(None, None, None, None, None, None, None, None)
        for file, conf in includes.items():
            # fastcgi.conf 和 fastcgi_params 识别
            if len(conf.get_directives()) == 0:
                continue
            only_fastcgi_param = all([d.get_name() == "fastcgi_param" for d in conf.get_directives()])
            script_filename = any([
                "SCRIPT_FILENAME" in d.get_parameters()
                for d in conf.find_directives("fastcgi_param", include=False, sub_block=False)
            ])
            if only_fastcgi_param:
                if script_filename:
                    ret.fastcgi_conf = conf
                    ret.fastcgi_conf.file_path = os.path.join(self._tmp_conf_path, "fastcgi.conf")
                else:
                    ret.fastcgi_params = conf
                    ret.fastcgi_params.file_path = os.path.join(self._tmp_conf_path, "fastcgi_params")

            # koi-utf koi-win win-utf 识别
            charset_map = conf.find_directives("charset_map", include=False, sub_block=False)
            if charset_map:
                charset_map = charset_map[0]
                if charset_map.get_parameters()[0] == "koi8-r":
                    if charset_map.get_parameters()[1] == "utf-8":
                        ret.koi_utf = conf
                        ret.koi_utf.file_path = os.path.join(self._tmp_conf_path, "koi-utf")
                        ret.koi_win = conf
                        ret.koi_win.file_path = os.path.join(self._tmp_conf_path, "koi-win")
                elif charset_map.get_parameters()[0] == "windows-1251" and charset_map.get_parameters()[1] == "utf-8":
                    ret.win_utf = conf
                    ret.win_utf.file_path = os.path.join(self._tmp_conf_path, "win-utf")

            # scgi_params 识别
            only_scgi_param = all([d.get_name() == "scgi_param" for d in conf.get_directives()])
            if only_scgi_param:
                ret.scgi_params = conf
                ret.scgi_params.file_path = os.path.join(self._tmp_conf_path, "scgi_params")

            # uwsgi_params 识别
            only_uwsgi_param = all([d.get_name() == "uwsgi_param" for d in conf.get_directives()])
            if only_uwsgi_param:
                ret.uwsgi_params = conf
                ret.uwsgi_params.file_path = os.path.join(self._tmp_conf_path, "uwsgi_params")

            # mimetypes.conf 识别
            only_mimetypes_conf = conf.directives and conf.directives[0].get_name() == "types" and len(
                conf.directives) == 1
            if only_mimetypes_conf:
                ret.mimetypes_conf = conf
                ret.mimetypes_conf.file_path = os.path.join(self._tmp_conf_path, "mime.types")

            # proxy_params 识别
            only_proxy_param = all([d.get_name() == "proxy_set_header" for d in conf.get_directives()])
            if only_proxy_param:
                ret.proxy_params = conf
                ret.proxy_params.file_path = os.path.join(self._tmp_conf_path, "proxy_params")

        return ret

    def try_get_other_nginx_conf(self):
        nginx_conf_dir =  os.path.dirname(self.nginx_main_conf_file)
        for attr, need_file in self.ng_org_cfg.org_config_names().items():
            if getattr(self.ng_org_cfg, attr) is not None:
                continue

            file = os.path.join(nginx_conf_dir, need_file)
            if not os.path.exists(file):
                continue
            try:
                org_c = parse_file(file, parse_include=False, main_config_path=self.nginx_main_conf_file)
                setattr(self.ng_org_cfg, attr, org_c)
            except Exception:
                continue


    def _format_sites(self):
        """
        格式化站点配置
        :return: None
        """
        sites = site_detector(self.config)  # 格式化站点配置
        for site in sites:
            if site.server_names == ['phpmyadmin']:  # phpmyadmin 跳过 会在主配置文件中处理
                self._format_php_site(site)  # 解析但不保留，每次重新生成符合宝塔的phpmyadmin配置
                continue
            if site.server_names == ["_"]:
                self.bt_conf.default_server = self._format_default_server(site)
                continue
            if len(site.server_names) == 1 and site.server_names[0] in ("127.0.0.1", "::1", "localhost") and \
                    len(site.server_blocks) == 1:
                server_block = site.server_blocks[0].get_block()
                if server_block and server_block.find_directives("stub_status", sub_block=True):
                    self.bt_conf.nginx_status_server = self._get_nginx_status_server(site)
                continue
            if site.site_type == SITE_TYPE_STATIC:
                self.bt_conf.sites_conf[tuple(site.server_names)] = self._format_static_site(site)
            elif site.site_type == SITE_TYPE_PHP:
                self.bt_conf.sites_conf[tuple(site.server_names)] = self._format_php_site(site)
            elif site.site_type == SITE_TYPE_PROXY:
                self.bt_conf.sites_conf[tuple(site.server_names)] = self._format_proxy_site(site)

    @staticmethod
    def read_site_name(site_info: SiteInfo) -> str:
        """
        获取站点名称, 获取server中的第一个合规的域名作为站点名称，此选项是Ip格式
        :param site_info: 站点(基础识别出来的站点信息)
        :return: 站点名称
        """
        domain_regex = re.compile(r"^(\*\.?)?([\u4e00-\u9fa5a-zA-Z0-9-]+)(\.[\u4e00-\u9fa5a-zA-Z0-9-]+)*(:\d+)?$")
        ip_names = []
        for server_name in site_info.server_names:
            if domain_regex.match(server_name):
                server_name = server_name.strip("*.")
                if "]:" in server_name:
                    server_name = server_name.rsplit(":")[0]
                elif ":" in server_name:
                    server_name = server_name.rsplit(":")[0]
                return server_name
            if _is_ip_domain(server_name):
                ip_names.append(server_name)
            if server_name in ("localhost", "127.0.0.1", "::1"):
                ip_names.append(server_name)

        return site_info.server_names[0] if not ip_names else ip_names[0]

    def read_site_path(self, site_info: SiteInfo) -> str:
        """
        获取站点路径, 获取站点根目录路径
        :param site_info: 站点(基础识别出来的站点信息)
        :return: 站点路径
        """
        # 如果有server层级的 root 指令，那么站点路径就是 root 指令的值
        # 如果没有server层级的 root 指令，那么这就是所有的子块中寻找 root 指令
        roo_path = "{}/html".format(self._working_dir)
        for srv in site_info.server_blocks:
            srv_block = srv.get_block()
            roots = srv_block.find_directives("root", include=True, sub_block=False)
            if not roots:
                roots = srv_block.find_directives("root", include=True, sub_block=True)

            if not roots:
                continue

            for r in roots:
                if r.get_parameters() and r.get_parameters()[0]:
                    tmp_roo_path = r.get_parameters()[0].strip("'").strip('"')
                    if "$" in tmp_roo_path:
                        tmp_roo_path = tmp_roo_path[:tmp_roo_path.index("$")]
                    if not tmp_roo_path.startswith("/"):
                        tmp_roo_path = os.path.join(self._working_dir, tmp_roo_path)
                    if os.path.exists(tmp_roo_path):
                        roo_path = tmp_roo_path

        dir_name = os.path.basename(roo_path)
        # 部分php项目的运行目录上层才是项目的根目录
        if os.path.basename(roo_path) in ("public", "webroot") and (os.path.isdir(
                os.path.join(dir_name, "vendor")
        ) or os.path.exists(os.path.join(dir_name, "config"))):
            roo_path = dir_name

        return roo_path

    def _format_static_site(self, site: SiteInfo) -> _StaticSite:
        """
        格式化静态站点配置
        :param site: 站点信息
        :return: None
        """
        name = self.read_site_name(site)
        site_path = self.read_site_path(site)
        if not name:
            raise ValueError("无法获取站点名称")
        ret_site = _StaticSite(
            name=name,
            site_path=site_path,
            site_names=site.server_names,
            config=Config(
                file_path=os.path.join(self._tmp_sites_path, "html_{}.conf".format(name)),
                directives=site.server_blocks
            ),
            ports=site.listen_ports
        )
        self.prep_block(ret_site)
        self.set_ssl_and_ext_and_rewrite(ret_site)
        return ret_site

    @staticmethod
    def read_proxy_info(site: SiteInfo):
        proxy_info = []
        for srv in site.server_blocks:
            srv_block = srv.get_block()
            for loc in srv_block.find_directives("location", include=True, sub_block=False):
                loc: Location = trans_(loc, Location)
                loc_block = loc.get_block()
                if not loc_block:
                    continue

                tmp_info = {}
                proxy_pass_l = loc_block.find_directives("proxy_pass", include=True, sub_block=False)
                if not proxy_pass_l:
                    continue
                tmp_info["path"] = loc.match
                tmp_info["proxy_pass"] = proxy_pass_l[0].get_parameters()[0]
                send_host = ""
                for proxy_set_header in loc_block.find_directives("proxy_set_header", include=True, sub_block=False):
                    if proxy_set_header.get_parameters()[0] == "Host":
                        send_host = proxy_set_header.get_parameters()[1]
                        break
                tmp_info["send_host"] = send_host
                proxy_info.append(tmp_info)
        return proxy_info

    def _format_proxy_site(self, site: SiteInfo) -> _ProxySite:
        """
        格式化反向代理站点配置
        :param site: 站点信息
        :return: None
        """
        name = self.read_site_name(site)
        site_path = self.read_site_path(site)
        proxy_info = self.read_proxy_info(site)
        root_proxy = dict()
        for info in proxy_info:
            if info["path"] == "/":
                root_proxy = info
                break
        if root_proxy:
            proxy_info.remove(root_proxy)
        ret_site = _ProxySite(
            name=name,
            site_path=site_path,
            site_names=site.server_names,
            config=Config(
                file_path=os.path.join(self._tmp_sites_path, "{}.conf".format(name)),
                directives=site.server_blocks
            ),
            proxy_info=proxy_info,
            root_proxy=root_proxy,
            ports=site.listen_ports,
        )
        self.prep_block(ret_site)
        self.set_ssl_and_ext_and_rewrite(ret_site)
        return ret_site

    def _format_php_site(self, site: SiteInfo) -> _PHPSite:
        """
        格式化PHP站点配置
        :param site: 站点信息
        :return: None
        """
        name = self.read_site_name(site)
        site_path = self.read_site_path(site)
        ret_site = _PHPSite(
            name=name,
            site_path=site_path,
            site_names=site.server_names,
            config=Config(
                file_path=os.path.join(self._tmp_sites_path, "{}.conf".format(name)),
                directives=site.server_blocks
            ),
            php_sock="",
            ports=site.listen_ports,
        )
        self.prep_block(ret_site)
        self.set_ssl_and_ext_and_rewrite(ret_site)
        self.set_php_info(ret_site)
        return ret_site

    def _format_default_server(self, site: SiteInfo = None):
        """
        格式化默认站点配置
        :return: None
        """
        if site:
            site_path = self.read_site_path(site)
            return _StaticSite(
                name="default",
                site_path=site_path,
                site_names=site.server_names,
                config=Config(
                    file_path=os.path.join(self._tmp_sites_path, "0.default.conf"),
                    directives=site.server_blocks
                ),
                ports=site.listen_ports,
            )
        else:
            # server
            # {
            #     listen 80;
            #     server_name _;
            #     index index.html;
            #     root /www/server/nginx/html;
            # }
            return _StaticSite(
                name="default",
                site_path="",
                site_names=[],
                config=Config(
                    file_path=os.path.join(self._tmp_sites_path, "0.default.conf"),
                    directives=[
                        Server(
                            name="server",
                            block=Block([
                                Directive(name="listen", parameters=["80"]),
                                Directive(name="server_name", parameters=["_"]),
                                Directive(name="index", parameters=["index.html"]),
                                Directive(name="root", parameters=["/www/server/nginx/html"])
                            ])
                        )
                    ]
                ),
                ports=[80],
            )

    def _get_nginx_status_server(self, site: SiteInfo = None):
        if site:
            site_path = self.read_site_path(site)
            return _StaticSite(
                name="default",
                site_path=site_path,
                site_names=site.server_names,
                config=Config(
                    file_path=os.path.join(self._tmp_sites_path, "phpfpm_status.conf"),
                    directives=site.server_blocks
                ),
                ports=site.listen_ports,
            )
        else:
            # server {
            #     listen 80;
            #     server_name 127.0.0.1;
            #     allow 127.0.0.1;
            #     location /nginx_status {
            #         stub_status on;
            #         access_log off;
            #     }
            # }
            return _StaticSite(
                name="default",
                site_path="",
                site_names=[],
                config=Config(
                    file_path=os.path.join(self._tmp_sites_path, "phpfpm_status.conf"),
                    directives=[
                        Server(
                            name="server",
                            block=Block([
                                Directive(name="listen", parameters=["80"]),
                                Directive(name="server_name", parameters=["127.0.0.1"]),
                                Directive(name="allow", parameters=["127.0.0.1"]),
                                Location(
                                    name="location",
                                    modifier="",
                                    match="",
                                    block=Block([
                                        Directive(name="stub_status", parameters=["on"]),
                                        Directive(name="access_log", parameters=["off"])
                                    ]),
                                    parameters=["/nginx_status"]
                                )
                            ])
                        )
                    ]
                ),
                ports=[80],
            )

    def _get_phpmyadmin_conf(self) -> Server:
        r"""server
    {
        listen 888;
        server_name phpmyadmin;
        index index.html index.htm index.php;
        root  /www/server/phpmyadmin;
            location ~ /tmp/ {
                return 403;
            }

        #error_page   404   /404.html;
        include enable-php.conf;

        location ~ .*\.(gif|jpg|jpeg|png|bmp|swf)$
        {
            expires      30d;
        }

        location ~ .*\.(js|css)?$
        {
            expires      12h;
        }

        location ~ /\.
        {
            deny all;
        }

        access_log  /www/wwwlogs/access.log;
    }"""
        enable_php_conf = Config(file_path=os.path.join(self._tmp_conf_path, "enable-php.conf"), directives=[])
        ret = Server(name="server", block=Block([
            Directive(name="listen", parameters=["888"]),
            Directive(name="server_name", parameters=["phpmyadmin"]),
            Directive(name="index", parameters=["index.html", "index.htm", "index.php"]),
            Directive(name="root", parameters=["/www/server/phpmyadmin"]),
            Location(
                name="location", modifier="~", match="/tmp/",
                parameters=["~", "/tmp/"], block=Block([
                    Directive(name="return", parameters=["403"])
                ])
            ),
            Include(name="include", include_path="enable-php.conf", parameters=["enable-php.conf"],
                    comment=["#error_page   404   /404.html;"], configs=[enable_php_conf]),
            Location(
                name="location", modifier="~",
                match=r".*\.(gif|jpg|jpeg|png|bmp|swf)$",
                parameters=["~", r".*\.(gif|jpg|jpeg|png|bmp|swf)$"],
                block=Block([
                    Directive(name="expires", parameters=["30d"])
                ])
            ),
            Location(
                name="location", modifier="~",
                match=r".*\.(js|css)?$",
                parameters=["~", r".*\.(js|css)?$"],
                block=Block([
                    Directive(name="expires", parameters=["12h"])
                ])
            ),
            Location(
                name="location",
                modifier="~",
                match=r"/\.",
                parameters=["~", r"/\."],
                block=Block([
                    Directive(name="deny", parameters=["all"])
                ])
            ),
            Directive(name="access_log", parameters=["/www/wwwlogs/access.log"])
        ]))

        nginx_conf = "/www/server/nginx/conf"
        if not os.path.exists(os.path.join(nginx_conf, "enable-php.conf")):
            os.makedirs(nginx_conf, 0o755, exist_ok=True)
            with open(os.path.join(nginx_conf, "enable-php.conf"), "w+") as f:
                f.write("")

        self.bt_conf.include_files[enable_php_conf.file_path] = enable_php_conf
        return ret

    def _build_main_other_conf(self):
        """
        构建主配置文件中和其他配置文件
        :return: None
        """
        # 遍历所有的配置文件，排除 server （站点）配置， 站点配置文件在站点部分集中处理
        # 除了nginx官方提供的配置，其他的用户自定义子配置文件会被直接添加到主配置文件中

        bt_main_conf = self.bt_conf.mian_conf
        http_conf_d = Include(name="include",
                              include_path="http_config.d/*.conf",
                              parameters=["http_config.d/*.conf"],
                              comment=["# http块的其他配置文件"], configs=[])
        has_http_conf_d = False

        def _read_block(
                b: Union[Block, Http, Config, Upstream],  # 待处理的配置块
                now_bock: Union[Block, Http, Config, Upstream],  # 当前要写入的配置块
                in_http: bool,  # 当前配置块是否在http块中
        ):
            for d in b.directives:
                if d.__class__ is Http:
                    d = trans_(d, Http)
                    http_b = d.get_block()
                    if not http_b:
                        continue
                    n_http = Http(servers=[], directives=[])
                    bt_main_conf.directives.append(n_http)
                    _read_block(d, n_http, in_http=True)
                elif d.__class__ is Include:
                    d = trans_(d, Include)
                    if not in_http:
                        now_bock.directives.append(d)
                        continue
                    else:
                        # 引入的是官方配置文件
                        if len(d.configs) == 1 and d.configs[0] in self.ng_org_cfg:
                            now_bock.directives.append(d)
                            continue

                        if len(d.configs) == 1 and d.configs[0].file_path in self.panel_nginx_http_d_conf:
                            now_bock.directives.append(d)
                            self.bt_conf.panel_http_conf_d.append(d.configs[0])
                            continue

                        http_conf_d_list = []
                        for c in d.configs:
                            # 过滤掉面板的http共用配置文件
                            if c.file_path in self.panel_vhost_http_d_conf:
                                if c not in self.bt_conf.panel_http_conf_d:
                                    self.bt_conf.panel_http_conf_d.append(c)
                                continue
                            # 没有server转移到 http_conf_d 配置中
                            if not c.find_directives("server", include=True):
                                http_conf_d_list.append(c)
                                if c.file_path in self.bt_conf.include_files:
                                    self.bt_conf.include_files.pop(c.file_path)
                            else:
                                if c.file_path in self.bt_conf.include_files:
                                    self.bt_conf.include_files.pop(c.file_path)
                                _read_block(trans_(c, Config), now_bock, in_http=in_http)
                        nonlocal has_http_conf_d
                        if http_conf_d_list:
                            if not has_http_conf_d:
                                has_http_conf_d = True
                                now_bock.directives.append(http_conf_d)
                            http_conf_d.configs.extend(http_conf_d_list)

                elif d.__class__ is Server:  # 暂时忽略server配置
                    continue
                else:
                    now_bock.directives.append(d)

        _read_block(self.config, bt_main_conf, in_http=False)
        file_name_set = set()
        if has_http_conf_d:
            for tmp_c in http_conf_d.configs:
                file_name = os.path.basename(tmp_c.file_path)
                if not file_name.endswith(".conf"):
                    file_name = file_name + ".conf"
                if file_name in file_name_set:
                    file_name = file_name[:-5] + "_" + str(len(file_name_set)) + ".conf"
                tmp_c.file_path = os.path.join(self.bt_conf.tmp_conf_path, "conf", "http_config.d", file_name)
                self.bt_conf.http_conf_d.append(tmp_c)

    def _get_bt_default_conf(self, ):
        """
        获取面板默认配置
        :return: 面板默认配置
        """

    @staticmethod
    def get_main_server(config: Config) -> Server:
        servers = config.find_directives("server", include=False, sub_block=False)
        if not servers:
            raise ValueError("no server directive found in main config")
        if len(servers) == 1:
            server = servers[0]
        else:
            server = None
            for srv in servers:
                srv_block = srv.get_block()
                if not srv_block:
                    continue
                listens = srv_block.find_directives("listen", include=False, sub_block=False)
                for listen in listens:
                    listen_params = listen.get_parameters() or []
                    has_ssl = any((param in ("443", "ssl", "quic") or ":443" in  param) for param in listen_params)
                    if has_ssl:
                        server = srv
                        break
                if server:
                    break
            if not server:
                server = servers[0]
        server = trans_(server, Server)
        if not server:
            raise ValueError("no server directive found in main config")

        main_server_listens = server.block.find_directives("listen", include=False, sub_block=False)
        ml_has_ssl = False
        ml_has_80 = False
        for ml in main_server_listens:
            listen_params = ml.get_parameters() or []
            has_ssl = any((param in ("443", "ssl", "quic") or ":443" in  param) for param in listen_params)
            ml_has_ssl = ml_has_ssl or has_ssl
            has_80 = any((":80" in param or param == "80") for param in listen_params)
            ml_has_80 = ml_has_80 or has_80

        if not ml_has_80 and ml_has_ssl and len(main_server_listens) ==1:
            server.block.directives.insert(0, Directive(name="listen", parameters=["80"]))

        config.directives.remove(server)
        config.directives.insert(0, server)
        return server

    @dataclass
    class FindFirst:  # 查找第一个指令
        directive: str = ""
        parameter: str = ""
        offset: int = 0

    class FindLast(FindFirst):  # 查找最后一个指令
        pass

    # 在sever块中查找指令
    @classmethod
    def _find_idx(cls, _block: Union[Block, Http, Config, Upstream], *ops: Union[FindFirst, FindLast], default: int = -1):
        directives = _block.get_directives()
        for op in ops:
            target_idx = -1
            for i, directive in enumerate(directives):
                if op.directive and op.directive == directive.get_name() and (
                        op.parameter == "" or any(op.parameter in p for p in directive.get_parameters())
                ):
                    target_idx = i
                    if type(op) is cls.FindFirst:
                        return target_idx + op.offset

            if target_idx >= 0:
                return target_idx + op.offset
        return default

    def set_ssl_and_ext_and_rewrite(self, site: Union[_PHPSite, _ProxySite, _StaticSite]):
        server = self.get_main_server(site.config)
        srv_block = server.get_block()
        # extension
        extension_conf_path = "/www/server/panel/vhost/nginx/extension/{}/*.conf".format(site.name)
        extension_conf_path_re = re.compile(r".*/vhost/nginx/extension/.*\*\.conf")
        extension_conf = server.top_find_directives_with_param("include", extension_conf_path_re)
        if not extension_conf:
            file_path = "{}/vhost/nginx/extension/{}/default.conf".format(self._tmp_path, site.name)
            ext_conf = Config(file_path=file_path, directives=[])
            extension_conf = [
                Include(
                    name="include",
                    block=None,
                    comment=[
                        "# 引入用户自定义扩展配置文件，请勿删除"
                    ],
                    parameters=[extension_conf_path],
                    include_path=extension_conf_path,
                    configs=[extension_conf]
                ),
            ]
            site.other_configs.append(ext_conf)
            idx = self._find_idx(
                srv_block,
                self.FindFirst("root", offset=1), self.FindFirst("server_name", offset=1), self.FindFirst("listen", offset=1),
                default=0,
            )
            srv_block.directives = srv_block.directives[:idx] + extension_conf + srv_block.directives[idx:]

        # ssl_certificate or ssl_certificate_key
        ssl_certificate = server.top_find_directives("ssl_certificate")
        ssl_certificate_key = server.top_find_directives("ssl_certificate_key")
        if not ssl_certificate and not ssl_certificate_key:
            for d in srv_block.get_directives():
                if "#error_page 404/404.html;" in d.get_comment():
                    break
            else:
                cert_idx = self._find_idx(
                    srv_block,
                    self.FindFirst("location", offset=-1),
                    self.FindFirst("root", offset=1), self.FindFirst("server_name", offset=1), self.FindFirst("listen", offset=1),
                    default=-1)
                cert_conf = [  # 只要备注
                    Directive(
                        name="",
                        parameters=[],
                        comment=[
                            "#SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则",
                            "#error_page 404/404.html;",
                            "#SSL-END",
                        ]
                    ),
                ]
                srv_block.directives = srv_block.directives[:cert_idx] + cert_conf + srv_block.directives[cert_idx:]
        else:
            min_d = None
            min_d_idx = len(srv_block.directives)
            max_d_idx = 0
            for d in ssl_certificate + ssl_certificate_key:
                idx = srv_block.directives.index(d)
                if min_d_idx > idx:
                    min_d_idx = idx
                    min_d = d
                if max_d_idx < idx:
                    max_d_idx = idx
            min_d = trans_(min_d, Directive)
            if "#error_page 404/404.html;" not in min_d.comment:
                min_d.comment += [
                    "# SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则",
                    "#error_page 404/404.html;"
                ]

            end_comment = Directive(
                name="",
                parameters=[],
                comment=[
                    "#SSL-END",
                ])

            srv_block.directives = srv_block.directives[:max_d_idx] + [end_comment] + srv_block.directives[max_d_idx:]

        # CERT-APPLY-CHECK
        apply_conf_path = "/www/server/panel/vhost/nginx/well-known/{}.conf".format(site.name)
        apply_conf_path_re = re.compile(r".*/vhost/nginx/well-known/.*\.conf")
        apply_conf = server.top_find_directives_with_param("include", apply_conf_path_re)
        if not apply_conf:
            ap_conf_file_path = "{}/vhost/nginx/well-known/{}.conf".format(self._tmp_path, site.name)
            ap_conf = Config(file_path=ap_conf_file_path, directives=[])
            apply_conf = [
                Include(
                    name="include",
                    parameters=[apply_conf_path],
                    comment=[
                        "#CERT-APPLY-CHECK--START",
                        "# 用于SSL证书申请时的文件验证相关配置 -- 请勿删除"
                    ],
                    configs=[ap_conf]
                ),
                Directive(name="", comment=["#CERT-APPLY-CHECK--END"])
            ]
            site.other_configs.append(ap_conf)
            idx = self._find_idx(
                srv_block,
                self.FindFirst("root", offset=1), self.FindFirst("index", offset=1), self.FindFirst("server_name", offset=1),
                default=0,
            )
            srv_block.directives = srv_block.directives[:idx] + apply_conf + srv_block.directives[idx:]

        # rewrite
        conf_pre = "{}_".format(site.site_type().lower())
        if conf_pre in ('php_', "proxy_"):
            conf_pre = ""
        rewrite_conf_path = "/www/server/panel/vhost/rewrite/{}{}.conf".format(conf_pre, site.name)
        rewrite_conf_path_re = re.compile(r".*/vhost/rewrite/.*\.conf")
        rewrite_conf = server.top_find_directives_with_param("include", rewrite_conf_path_re)
        if not rewrite_conf:
            file_path = "{}/vhost/rewrite/{}{}.conf".format(self._tmp_path, conf_pre, site.name)
            the_rewrite_cconf = Config(file_path=file_path, directives=[])
            rewrite_conf = [
                Include(
                    name="include",
                    block=None,
                    comment=[ "#REWRITE-START URL重写规则引用,修改后将导致面板设置的伪静态规则失效"],
                    parameters=[rewrite_conf_path],
                    include_path=rewrite_conf_path,
                    configs=[the_rewrite_cconf]
                ),
                Directive(
                    name="",
                    parameters=[],
                    comment=[
                        "#REWRITE-END"
                    ]
                )
            ]
            site.other_configs.append(the_rewrite_cconf)
            idx = self._find_idx(
                srv_block,
                self.FindFirst("location", offset=1),
                self.FindFirst("root", offset=1), self.FindFirst("server_name", offset=1), self.FindFirst("listen", offset=1),
                default=0,
            )
            srv_block.directives = srv_block.directives[:idx] + rewrite_conf + srv_block.directives[idx:]


    def get_fastcgi_conf(self):
        """
        fastcgi_param  SCRIPT_FILENAME    $document_root$fastcgi_script_name;
        fastcgi_param  QUERY_STRING       $query_string;
        fastcgi_param  REQUEST_METHOD     $request_method;
        fastcgi_param  CONTENT_TYPE       $content_type;
        fastcgi_param  CONTENT_LENGTH     $content_length;

        fastcgi_param  SCRIPT_NAME        $fastcgi_script_name;
        fastcgi_param  REQUEST_URI        $request_uri;
        fastcgi_param  DOCUMENT_URI       $document_uri;
        fastcgi_param  DOCUMENT_ROOT      $document_root;
        fastcgi_param  SERVER_PROTOCOL    $server_protocol;
        fastcgi_param  REQUEST_SCHEME     $scheme;
        fastcgi_param  HTTPS              $https if_not_empty;

        fastcgi_param  GATEWAY_INTERFACE  CGI/1.1;
        fastcgi_param  SERVER_SOFTWARE    nginx/$nginx_version;

        fastcgi_param  REMOTE_ADDR        $remote_addr;
        fastcgi_param  REMOTE_PORT        $remote_port;
        fastcgi_param  REMOTE_USER        $remote_user;
        fastcgi_param  SERVER_ADDR        $server_addr;
        fastcgi_param  SERVER_PORT        $server_port;
        fastcgi_param  SERVER_NAME        $server_name;

        # PHP only, required if PHP was built with --enable-force-cgi-redirect
        fastcgi_param  REDIRECT_STATUS    200;
        """
        if self.ng_org_cfg.fastcgi_conf:
            if not self.ng_org_cfg.fastcgi_conf.file_path.startswith(self._tmp_conf_path):
                self.ng_org_cfg.fastcgi_conf.file_path = os.path.join(self._tmp_conf_path, "fastcgi.conf")
            return self.ng_org_cfg.fastcgi_conf

        # 如果没有
        fastcgi_conf = Config(
            directives=[
                Directive(0, None, "fastcgi_param", [""], [],
                          ["SCRIPT_FILENAME", "$document_root$fastcgi_script_name"]),
                Directive(0, None, "fastcgi_param", [], [], ["QUERY_STRING", "$query_string"]),
                Directive(0, None, "fastcgi_param", [], [], ["REQUEST_METHOD", "$request_method"]),
                Directive(0, None, "fastcgi_param", [], [], ["CONTENT_TYPE", "$content_type"]),
                Directive(0, None, "fastcgi_param", [], [], ["CONTENT_LENGTH", "$content_length"]),
                Directive(0, None, "fastcgi_param", [""], [], ["SCRIPT_NAME", "$fastcgi_script_name"]),
                Directive(0, None, "fastcgi_param", [], [], ["REQUEST_URI", "$request_uri"]),
                Directive(0, None, "fastcgi_param", [], [], ["DOCUMENT_URI", "$document_uri"]),
                Directive(0, None, "fastcgi_param", [], [], ["DOCUMENT_ROOT", "$document_root"]),
                Directive(0, None, "fastcgi_param", [], [], ["SERVER_PROTOCOL", "$server_protocol"]),
                Directive(0, None, "fastcgi_param", [], [], ["REQUEST_SCHEME", "$scheme"]),
                Directive(0, None, "fastcgi_param", [], [], ["HTTPS", "$https if_not_empty"]),
                Directive(0, None, "fastcgi_param", [""], [], ["GATEWAY_INTERFACE", "CGI/1.1"]),
                Directive(0, None, "fastcgi_param", [], [], ["SERVER_SOFTWARE", "nginx/$nginx_version"]),
                Directive(0, None, "fastcgi_param", [""], [], ["REMOTE_ADDR", "$remote_addr"]),
                Directive(0, None, "fastcgi_param", [], [], ["REMOTE_PORT", "$remote_port"]),
                Directive(0, None, "fastcgi_param", [], [], ["REMOTE_USER", "$remote_user"]),
                Directive(0, None, "fastcgi_param", [], [], ["SERVER_ADDR", "$server_addr"]),
                Directive(0, None, "fastcgi_param", [], [], ["SERVER_PORT", "$server_port"]),
                Directive(0, None, "fastcgi_param", [], [], ["SERVER_NAME", "$server_name"]),
                Directive(0, None, "fastcgi_param", [
                    "",
                    "# PHP only, required if PHP was built with --enable-force-cgi-redirect"
                ], [], ["REDIRECT_STATUS", "200"])
            ],
            is_lua_block=False,
            file_path=os.path.join(self._tmp_conf_path, "fastcgi.conf")
        )
        self.ng_org_cfg.fastcgi_conf = fastcgi_conf
        return fastcgi_conf

    def bt_conf_by_key(self, key: str) -> Config:
        if key in self.bt_conf.bt_default_conf:
            return self.bt_conf.bt_default_conf[key]

        if key == "pathinfo.conf":
            # set $real_script_name $fastcgi_script_name;
            # if ($fastcgi_script_name ~ "^(.+?\.php)(/.+)$") {
            # set $real_script_name $1;
            # set $path_info $2;
            # }
            # fastcgi_param
            # SCRIPT_FILENAME $document_root$real_script_name;
            # fastcgi_param
            # SCRIPT_NAME $real_script_name;
            # fastcgi_param
            # PATH_INFO $path_info;
            pathinfo_conf = Config(
                file_path=os.path.join(self._tmp_conf_path, "pathinfo.conf"),
                directives=[
                    Directive(name="set", parameters=["$real_script_name", "$fastcgi_script_name"]),
                    Directive(
                        name="if", parameters=["(", "$fastcgi_script_name", "~", "\"^(.+?\\.php)(/.+)$\"", ")"],
                        block=Block(
                            directives=[
                                Directive(name="set", parameters=["$real_script_name", "$1"]),
                                Directive(name="set", parameters=["$path_info", "$2"]),
                            ]
                        )
                    ),
                    Directive(name="fastcgi_param", parameters=["SCRIPT_FILENAME", "$document_root$real_script_name"]),
                    Directive(name="fastcgi_param", parameters=["SCRIPT_NAME", "$real_script_name"]),
                    Directive(name="fastcgi_param", parameters=["PATH_INFO", "$path_info"])
                ]
            )
            self.bt_conf.bt_default_conf[key] = pathinfo_conf
            return pathinfo_conf

        # 已废弃！！！！！！
        elif key == "proxy.conf":
            # proxy_temp_path /www/server/nginx/proxy_temp_dir;
            # proxy_cache_path /www/server/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:20m inactive=1d max_size=5g;
            # client_body_buffer_size 512k;
            # proxy_connect_timeout 60;
            # proxy_read_timeout 60;
            # proxy_send_timeout 60;
            # proxy_buffer_size 32k;
            # proxy_buffers 4 64k;
            # proxy_busy_buffers_size 128k;
            # proxy_temp_file_write_size 128k;
            # proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
            # proxy_cache cache_one;
            proxy_conf = Config(
                file_path=os.path.join(self._tmp_conf_path, "proxy.conf"),
                directives=[
                    Directive(name="proxy_temp_path", parameters=["proxy_temp_dir"]),
                    Directive(name="proxy_cache_path", parameters=[
                        "proxy_cache_dir",
                        "levels=1:2",
                        "keys_zone=cache_one:20m",
                        "inactive=1d",
                        "max_size=5g"
                    ]),
                    Directive(name="client_body_buffer_size", parameters=["512k"]),
                    Directive(name="proxy_connect_timeout", parameters=["60"]),
                    Directive(name="proxy_read_timeout", parameters=["60"]),
                    Directive(name="proxy_send_timeout", parameters=["60"]),
                    Directive(name="proxy_buffer_size", parameters=["32k"]),
                    Directive(name="proxy_buffers", parameters=["4", "64k"]),
                    Directive(name="proxy_busy_buffers_size", parameters=["128k"]),
                    Directive(name="proxy_temp_file_write_size", parameters=["128k"]),
                    Directive(name="proxy_next_upstream", parameters=[
                        "error", "timeout", "invalid_header", "http_500", "http_503", "http_404"
                    ]),
                    Directive(name="proxy_cache", parameters=["cache_one"])
                ]
            )
            self.bt_conf.bt_default_conf[key] = proxy_conf
            return proxy_conf

        raise ValueError("没有找到对应的配置文件")

    def _build_proxy_conf(self, exclude_directives: List[str] = None):
        exclude_directives = exclude_directives or []
        # proxy_temp_path /www/server/nginx/proxy_temp_dir;
        # proxy_cache_path /www/server/nginx/proxy_cache_dir levels=1:2 keys_zone=cache_one:20m inactive=1d max_size=5g;
        # client_body_buffer_size 512k;
        # proxy_connect_timeout 60;
        # proxy_read_timeout 60;
        # proxy_send_timeout 60;
        # proxy_buffer_size 32k;
        # proxy_buffers 4 64k;
        # proxy_busy_buffers_size 128k;
        # proxy_temp_file_write_size 128k;
        # proxy_next_upstream error timeout invalid_header http_500 http_503 http_404;
        # proxy_cache cache_one;
        directives = [
            Directive(name="proxy_temp_path", parameters=["/www/server/nginx/proxy_temp_dir"]),
            Directive(name="proxy_cache_path", parameters=[
                "/www/server/nginx/proxy_cache_dir",
                "levels=1:2",
                "keys_zone=cache_one:20m",
                "inactive=1d",
                "max_size=5g"
            ]),
            Directive(name="client_body_buffer_size", parameters=["512k"]),
            Directive(name="proxy_connect_timeout", parameters=["60"]),
            Directive(name="proxy_read_timeout", parameters=["60"]),
            Directive(name="proxy_send_timeout", parameters=["60"]),
            Directive(name="proxy_buffer_size", parameters=["32k"]),
            Directive(name="proxy_buffers", parameters=["4", "64k"]),
            Directive(name="proxy_busy_buffers_size", parameters=["128k"]),
            Directive(name="proxy_temp_file_write_size", parameters=["128k"]),
            Directive(name="proxy_next_upstream", parameters=[
                "error", "timeout", "invalid_header", "http_500", "http_503", "http_404"
            ]),
            Directive(name="proxy_cache", parameters=["cache_one"])
        ]
        proxy_conf = Config(
            file_path=os.path.join(self._tmp_conf_path, "proxy.conf"),
            directives=[d for d in directives if d.name not in exclude_directives]
        )
        self.bt_conf.bt_default_conf["proxy.conf"] = proxy_conf
        return proxy_conf

    def prep_block(self, site: Union[_StaticSite, _PHPSite, _ProxySite]):
        server = self.get_main_server(site.config)

        #
        def _prep_block(
                b: Union[Block, Config],  # 待处理的配置块
                now_bock: Union[Block, Config],  # 当前要写入的配置块
        ):
            for d in b.directives:
                if d.__class__ is Include:
                    d = trans_(d, Include)
                    # 引入的是官方配置文件
                    if len(d.configs) == 1 and d.configs[0] in self.ng_org_cfg:
                        now_bock.directives.append(d)
                        continue

                    # 引入的是宝塔的配置文件
                    if d.include_path.startswith("/www/server/panel/vhost/"):
                        for c in d.configs:
                            c.file_path = os.path.join(
                                self._tmp_path, "vhost",
                                c.file_path[len("/www/server/panel/vhost/"):]
                            )
                            self.bt_conf.include_files[c.file_path] = c
                        now_bock.directives.append(d)
                        continue

                    # 引入的是用户配置文件
                    for c in d.configs:
                        if c.file_path in self.bt_conf.include_files:
                            self.bt_conf.include_files.pop(c.file_path)
                        _prep_block(trans_(c, Config), now_bock)
                    continue

                sub_blok = d.get_block()
                if sub_blok and isinstance(sub_blok, (Block, Config)):
                    _sub_new_block = Block(directives=[])
                    _prep_block(sub_blok, _sub_new_block)
                    setattr(d, "block", _sub_new_block)

                now_bock.directives.append(d)

        new_server = Server(name="server", block=Block(directives=[]))
        _prep_block(server.get_block(), new_server.block)

        site.config.directives.remove(server)
        site.config.directives.append(new_server)

    def set_php_info(self, site: _PHPSite):
        server = self.get_main_server(site.config)
        # 处理配置
        locs = server.top_find_directives_with_param("location", "~", re.compile(r".*\\\.php.*"))
        php_sock, php_loc = None, None
        for loc in locs:
            loc_b: Optional[Block] = loc.get_block()
            if not loc_b:
                continue
            fastcgi_pass = loc_b.find_directives("fastcgi_pass", include=False, sub_block=False)
            if fastcgi_pass and fastcgi_pass[0].get_parameters():
                php_sock = fastcgi_pass[0].get_parameters()[0]
                php_loc = loc

            if php_sock:
                break

        if not php_sock:
            if site.site_names == ["phpmyadmin"]:
                return
            raise Exception("未找到php-fpm的socket")

        site.php_sock = php_sock
        idx = server.block.directives.index(php_loc)
        if php_sock in self.panel_php_info_sock:  # 使用的是面板php，则直接改为面板配置
            server.block.directives[idx] = Include(
                name="include",
                include_path=self.panel_php_info_sock[php_sock],
                parameters=[self.panel_php_info_sock[php_sock]],
                configs=[]
            )
            return

        php_other = os.path.join(self._tmp_path, "vhost/other_php", site.name, "enable-php-other.conf")
        # location ~ [^/]\.php(/|$)
        # {
        #     try_files $uri =404;
        #     fastcgi_pass  unix:/tmp/php-cgi-83.sock;
        #     fastcgi_index index.php;
        #     include fastcgi.conf;
        #     include pathinfo.conf;
        # }
        php_other_conf = Config(file_path=php_other, directives=[Location(
            name="location",
            parameters=["~", r"[^/]\.php(/|$)"],
            block=Block(directives=[
                Directive(name="try_files", parameters=["$uri", "=404"]),
                Directive(name="fastcgi_pass", parameters=[php_sock]),
                Directive(name="fastcgi_index", parameters=["index.php"]),
                Include(name="include", include_path="fastcgi.conf", parameters=["fastcgi.conf"],
                        configs=[self.get_fastcgi_conf()]),
                Include(name="include", include_path="pathinfo.conf", parameters=["pathinfo.conf"],
                        configs=[self.bt_conf_by_key("pathinfo.conf")])
            ])
        )])
        site.other_configs.append(php_other_conf)
        args_path = "/www/server/panel/vhost/other_php/{}/enable-php-other.conf".format(site.name)
        server.block.directives[idx] = Include(
            name="include",
            include_path=args_path,
            parameters=[args_path],
            configs=[php_other_conf]
        )

        return

    def _set_bt_nginx_values(self):
        # worker_processes worker_connections keepalive_timeout gzip gzip_min_length gzip_comp_level
        # client_max_body_size server_names_hash_bucket_size client_header_buffer_size
        # worker_processes
        worker_processes_list = self.bt_conf.mian_conf.find_directives("worker_processes", include=True, sub_block=False)
        if worker_processes_list:
            mian_worker_processes = worker_processes_list[0]
            if mian_worker_processes not in self.bt_conf.mian_conf.directives:
                new_mian_w_p = Directive(
                    name=mian_worker_processes.get_name(),
                    parameters=mian_worker_processes.get_parameters(),
                    comment=mian_worker_processes.get_comment(),
                    inline_comment=mian_worker_processes.get_inline_comment()
                )
                self.bt_conf.mian_conf.directives.insert(0, new_mian_w_p)
                d = trans_(mian_worker_processes, Directive)  # 将不在主配置文件中的worker_processes设置为空
                d.name = ""
                d.parameters = []
                d.comment = []
                d.inline_comment = []
        else:
            new_mian_w_p = Directive(
                name="worker_processes",
                parameters=["auto"],
            )
            self.bt_conf.mian_conf.directives.insert(0, new_mian_w_p)

        http = self.bt_conf.mian_conf.find_http()

        # worker_connections
        events_list = self.bt_conf.mian_conf.find_directives("events")
        if events_list:
            events = events_list[0]
            events_block = events.get_block()
            if events not in self.bt_conf.mian_conf.directives:
                new_events = Directive(
                    name="events",
                    parameters=[],
                    comment=events.get_comment(),
                    inline_comment=events.get_inline_comment(),
                    block=events_block
                )
                http_index = self.bt_conf.mian_conf.directives.index(events)
                self.bt_conf.mian_conf.directives.insert(http_index, new_events)
                d = trans_(events, Directive)  # 清空其他配置中的event 移动到主配置中
                d.name = ""
                d.parameters = []
                d.comment = []
                d.inline_comment = []
                d.block = None
                # 赋值替换为主配置文件中的events
                events = new_events

            if events_block:
                worker_connections = events_block.find_directives("worker_connections")
                if not worker_connections:
                    events_block.get_directives().insert(0, Directive(
                        name="worker_connections",
                        parameters=["51200"]
                    ))
            else:
                events_block = Block(directives=[
                    Directive(
                        name="worker_connections",
                        parameters=["51200"]
                    )
                ])
                events.block = events_block


        http_bt_value = [
            ("client_header_buffer_size", ["32k"]),
            ("server_names_hash_bucket_size", ["512"]),
            ("client_max_body_size", ["50m"]),
            ("gzip_comp_level", ["5"]),
            ("gzip_min_length", ["1k"]),
            ("gzip", ["off"]),
            ("keepalive_timeout", ["60"]),
        ]
        http = self.bt_conf.mian_conf.find_http()

        for d_name, d_default in http_bt_value:
            key_list = http.find_directives(d_name, include=True)
            if key_list:
                key = key_list[0]
                if key not in http.directives:
                    new_kt = Directive(
                        name=d_name,
                        parameters=key.get_parameters(),
                        comment=key.get_comment(),
                        inline_comment=key.get_inline_comment()
                    )

                    http.directives.insert(0, new_kt)
                    old_kt = trans_(key, Directive) # 移动到主配置文件中
                    old_kt.name = ""
                    old_kt.parameters = []
                    old_kt.comment = []
                    old_kt.inline_comment = []
                    old_kt.block = None
                    key = new_kt
            else:
                new_kt = Directive(
                    name=d_name,
                    parameters=d_default
                )
                http.directives.insert(0, new_kt)


    def _set_main_bt_conf(self):
        # nginx value => 性能调整相关
        self._set_bt_nginx_values()
        # pid-file
        pid_ds = self.bt_conf.mian_conf.find_directives("pid", sub_block=False, include=True)
        if pid_ds:
            pid_d = trans_(pid_ds[0], Directive)
            pid_d.parameters = ["/www/server/nginx/logs/nginx.pid"]
            for other_pid in pid_ds[1:]:
                self.bt_conf.mian_conf.directives.remove(other_pid)
        # error_log
        error_log_ds = self.bt_conf.mian_conf.find_directives("error_log", sub_block=False, include=True)
        if error_log_ds:
            error_log_d = trans_(error_log_ds[0], Directive)
            if len(error_log_d.parameters) > 1:
                error_log_d.parameters[0]= "/www/wwwlogs/nginx_error.log"
            else:
                error_log_d.parameters = ["/www/wwwlogs/nginx_error.log"]

        # proxy.conf
        http = self.bt_conf.mian_conf.find_http()
        has_proxy_conf = any(["proxy.conf" in (i.get_parameters() or []) for i in http.find_directives("include")])
        # 不可重复指令 proxy_temp_path，client_body_buffer_size，proxy_cache，proxy_connect_timeout
        has_proxy_directives = 0
        proxy_directives = (
            "proxy_temp_path",
            "proxy_cache_path",
            "client_body_buffer_size",
            "proxy_connect_timeout",
            "proxy_read_timeout",
            "proxy_send_timeout",
            "proxy_buffer_size",
            "proxy_buffers",
            "proxy_busy_buffers_size",
            "proxy_temp_file_write_size",
            "proxy_next_upstream",
            "proxy_cache",
        )
        exclude_directives = []
        for d_name in proxy_directives:
            if http.find_directives(d_name, include=True, sub_block=False):
                exclude_directives.append(d_name)
        if not has_proxy_conf:
            if "proxy_cache_path" in exclude_directives:
                exclude_directives.append("proxy_cache")
            proxy_conf = self._build_proxy_conf(exclude_directives=exclude_directives)
            self.bt_conf.include_files[proxy_conf.file_path] = proxy_conf
            http.directives.append(
                Include(name="include", include_path="proxy.conf", parameters=["proxy.conf"], configs=[proxy_conf])
            )

        # 设置 流量限制共享缓存的配置
        # limit_conn_zone $binary_remote_addr zone=perip:10m; limit_conn_zone $server_name zone=perserver:10m;
        limit_conn_zone_list = http.find_directives("limit_conn_zone", sub_block=False, include=True)
        perip_ok = perserver_ok = False
        for tmp_limit_conn_zone in limit_conn_zone_list:
            if not len(tmp_limit_conn_zone.get_parameters()) == 2:
                continue
            nginx_var, zone = tmp_limit_conn_zone.get_parameters()
            if nginx_var == "$binary_remote_addr" and zone.startswith("zone=perip:"):
                perip_ok = True
            if nginx_var == "$server_name" and zone.startswith("zone=perserver:"):
                perserver_ok = True

        if not perip_ok:
            http.directives.append(Directive(
                name="limit_conn_zone",
                parameters=["$binary_remote_addr", "zone=perip:10m"]
            ))
        if not perserver_ok:
            http.directives.append(Directive(
                name="limit_conn_zone",
                parameters=["$server_name", "zone=perserver:10m"]
            ))

        # set php_myadmin config
        php_myadmin = self._get_phpmyadmin_conf()
        http.directives.append(php_myadmin)

        # include vhost/nginx
        http.directives.append(
            Include(
                name="include",
                include_path="/www/server/panel/vhost/nginx/*.conf",
                parameters=["/www/server/panel/vhost/nginx/*.conf"],
                configs=[]
            )  # 不实际引入
        )
        return

    def _replace_panel_http_conf(self):
        panel_path = "/www/server/panel"
        nginx_path = "/www/server/nginx"
        for conf in self.bt_conf.panel_http_conf_d:
            conf.file_path = conf.file_path.replace(panel_path, self._tmp_path).replace(nginx_path, self._tmp_path)


class _ConfileLink:

    @staticmethod
    def _walk_set_copy(tmp_path: str, target_path: str, filter_list: List[str] = None):
        filter_list = filter_list or []
        for root, dirs, files in os.walk(tmp_path):
            for file in files:
                this_file = root + "/" + file
                if this_file in filter_list:
                    continue
                real_dir = root.replace(tmp_path, target_path)
                if not os.path.isdir(real_dir):
                    os.makedirs(real_dir)

                real_file = real_dir + "/" + file
                if not os.path.exists(real_file):
                    with open(real_file, "w+") as f:
                        f.write("")

                os.rename(real_file, real_file + ".bak")
                shutil.copyfile(this_file, real_file)


    @staticmethod
    def _walk_reset_copy(tmp_path: str, target_path: str, filter_list: List[str] = None):
        filter_list = filter_list or []
        for root, dirs, files in os.walk(tmp_path):
            for file in files:
                this_file = root + "/" + file
                if this_file in filter_list:
                    continue
                real_dir = root.replace(tmp_path, target_path)
                real_file = real_dir + "/" + file
                if os.path.exists(real_file + ".bak"):
                    if os.path.exists(real_file):
                        os.remove(real_file)
                    os.rename(real_file + ".bak", real_file)
                    if os.path.getsize(real_file) == 0:
                        os.remove(real_file)

    # files_filter 从临时目录中过滤调指定文件
    def __init__(self, *path2path: Tuple[str, str], files_filter: List[str] = None):
        self.path2path_list = path2path
        if not files_filter:
            files_filter = []
        self.files_filter = files_filter

    def set_to(self):
        for path, target_path in self.path2path_list:
            self._walk_set_copy(path, target_path, self.files_filter)

    def reset_from(self):
        for path, target_path in self.path2path_list:
            self._walk_reset_copy(path, target_path, self.files_filter)

    def __enter__(self):
        self.set_to()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.reset_from()


def bt_nginx_format(ng_instance: NginxInstance, tmp_path: str = "./") -> BtNginxConf:
    f = _Formatter(ng_instance, tmp_conf_path=tmp_path)
    ret = f.to_bt_config()
    ret.save_conf()
    # ret.test_nginx(ng_instance.nginx_bin)
    return ret
