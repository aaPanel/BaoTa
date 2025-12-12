# 格式化为符合面板要求的站点配置
import os
import re
import subprocess
import time
import ipaddress
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional, Any, Union, Callable

from pygments.lexer import include

from .. import Config, Server, Parser, Lexer, trans_, Location, Directive, Block, dump_config, Include, \
    Http, Upstream, dump_block
from .site_detector import site_detector, SiteInfo, SITE_TYPE_STATIC, SITE_TYPE_PHP, SITE_TYPE_PROXY


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


@dataclass
class _StaticSite:
    """
    静态站点
    """
    name: str
    site_path: str
    site_names: List[str]
    config: Config  # 站点配置


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


@dataclass
class NgOrgConf:
    """
    存储识别出来的官方配置文件 (
    fastcgi.conf  fastcgi_params koi-utf koi-win mimetypes.conf scgi_params uwsgi_params win-utf
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

    def __contains__(self, item):
        attr = (
            "fastcgi_conf", "fastcgi_params", "koi_utf", "koi_win",
            "win_utf", "scgi_params", "uwsgi_params", "mimetypes_conf"
        )
        for attr in attr:
            if getattr(self, attr) and getattr(self, attr) == item:
                return True
        return False


# 存放转化中的数据
@dataclass
class BtNginxConf:
    """
    面板要求的Nginx站点配置格式
    """
    tmp_conf_path: str # 临时配置文件保存路径
    mian_conf: Config
    sites_conf: Dict[Tuple[str, ...], Union[_StaticSite, _PHPSite, _ProxySite]]
    default_server: Optional[_StaticSite]
    nginx_status_server: Optional[_StaticSite]
    include_files:Dict[str, Config]  # 存储需要复制并引用的配置文件
    bt_default_conf: Dict[str, Config]  # 存储面板默认配置文件

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
        print(f"==>{self.mian_conf.file_path}<==")
        self._write_conf(self.mian_conf)
        for file_path, config in self.include_files.items():
            print(f"==>{config.file_path}<==")
            self._write_conf(config)
        for site in self.sites_conf.values():
            print(f"==>{site.config.file_path}<==")
            self._write_conf(site.config)
        for k, config in self.bt_default_conf.items():
            if config.file_path in self.include_files:
                continue
            print(f"==>{config.file_path}<==")
            self._write_conf(config)

        if self.default_server:
            print(f"==>{self.default_server.config.file_path}<==")
            self._write_conf(self.default_server.config)
        if self.nginx_status_server:
            print(f"==>{self.nginx_status_server.config.file_path}<==")
            self._write_conf(self.nginx_status_server.config)


class _Formatter:
    """
    格式化器
    """

    def __init__(self, nginx_main_conf_file: str, tmp_conf_path: str = "./"):
        """
        初始化格式化器
        :param nginx_main_conf_file: Nginx主配置文件路径
        """
        if not os.path.isdir(tmp_conf_path):
            os.makedirs(tmp_conf_path)
        tmp_conf_path = os.path.join(tmp_conf_path, "bt_nginx_format_{}".format(int(time.time())))
        self._tmp_path = tmp_conf_path
        self._tmp_conf_path = os.path.join(tmp_conf_path, "conf")
        self._tmp_sites_path = os.path.join(tmp_conf_path, "vhost/nginx")

        self.nginx_main_conf_file = nginx_main_conf_file
        if not os.path.exists(nginx_main_conf_file):
            raise FileNotFoundError(f"nginx main conf file not found: {nginx_main_conf_file}")
        with open(nginx_main_conf_file, "r") as f:
            config_content = f.read()
        l = Lexer(config_content, nginx_main_conf_file)
        self.parser = Parser(l, parse_include=True, main_config_path=nginx_main_conf_file)
        self.config = self.parser.parse()
        self.config_includes = self.parser.parsed_includes
        self.no_server_includes = self._filter_no_server_includes(self.config_includes)
        self.ng_org_cfg = self._filter_nginx_org_config(self.config_includes)  # 被使用的官方配置文件

        self.bt_conf = BtNginxConf(
            tmp_conf_path=self._tmp_path,
            mian_conf=Config(
                directives=[],
                file_path=os.path.join(self._tmp_conf_path, "nginx.conf")
            ),  # 空的主配置文件，待后续填充
            sites_conf={},  # 站点配置，key为站点域名元组，value为SiteInfo
            default_server=None,
            nginx_status_server=None,
            include_files=self.no_server_includes,
            bt_default_conf={},
        )

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
            only_mimetypes_conf = conf.directives and conf.directives[0].get_name() == "types" and len(conf.directives) == 1
            if only_mimetypes_conf:
                ret.mimetypes_conf = conf
                ret.mimetypes_conf.file_path = os.path.join(self._tmp_conf_path, "mime.types")

        return ret

    def _format_sites(self):
        """
        格式化站点配置
        :return: None
        """
        sites = site_detector(self.config)  # 格式化站点配置
        for site in sites:
            if site.server_names == ['phpmyadmin']:  # phpmyadmin 跳过 会在主配置文件中处理
                self._format_php_site(site) # 解析但不保留，每次重新生成符合宝塔的phpmyadmin配置
                continue
            if site.server_names == ["_"]:
                self.bt_conf.default_server = self._format_default_server(site)
                continue
            if len(site.server_names) == 1 and site.server_names[0] in ("127.0.0.1", "::1", "localhost") and \
                    len(site.server_blocks) ==1:
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
        domain_regex = re.compile(r"^(([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,63})$")
        ip_names = []
        for server_name in site_info.server_names:
            if domain_regex.match(server_name):
                return server_name
            if _is_ip_domain(server_name):
                ip_names.append(server_name)
            if server_name in ("localhost", "127.0.0.1", "::1"):
                ip_names.append(server_name)

        return "" if not ip_names else ip_names[0]

    @staticmethod
    def read_site_path(site_info: SiteInfo) -> str:
        """
        获取站点路径, 获取站点根目录路径
        :param site_info: 站点(基础识别出来的站点信息)
        :return: 站点路径
        """
        # 如果有server层级的 root 指令，那么站点路径就是 root 指令的值
        # 如果没有server层级的 root 指令，那么这就是所有的子块中寻找 root 指令
        roo_path = ""
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
                    if not os.path.isabs(tmp_roo_path):
                        raise ValueError(
                            "网站root配置项不是绝对路径，不支持解析，"
                            "root path is not absolute: {}".format(r.get_parameters()[0])
                        )
                    if os.path.exists(tmp_roo_path):
                        roo_path = tmp_roo_path

        if not roo_path:
            return ""

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
                file_path=os.path.join(self._tmp_sites_path, "{}.conf".format(name)),
                directives=site.server_blocks
            )
        )
        self.prep_block(ret_site)
        self.set_ssl_and_ext(ret_site)
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
            root_proxy=root_proxy
        )
        self.prep_block(ret_site)
        self.set_ssl_and_ext(ret_site)
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
            php_sock=""
        )
        self.prep_block(ret_site)
        self.set_php_info(ret_site)
        self.set_ssl_and_ext(ret_site)
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
                )
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
                )
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
                )
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
                )
            )

    def _get_phpmyadmin_conf(self) -> Server:
        """server
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

                        # 引入的是用户自定义配置文件，但不包含server配置
                        no_server = not any([c.find_directives("server", include=True) for c in d.configs])
                        if no_server:
                            for c in d.configs:
                                # 将配置文件接管到 主配置文件的同级目录
                                c.file_path = os.path.join(self._tmp_conf_path, os.path.basename(d.include_path))
                            d.include_path = os.path.basename(d.include_path)
                            now_bock.directives.append(d)
                            continue
                        else:
                            for c in d.configs:
                                if c.file_path in self.bt_conf.include_files:
                                    self.bt_conf.include_files.pop(c.file_path)
                                _read_block(trans_(c, Config), now_bock, in_http=in_http)
                elif d.__class__ is Server:  # 暂时忽略server配置
                    continue
                else:
                    now_bock.directives.append(d)

        _read_block(self.config, bt_main_conf, in_http=False)

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
                    for param in (listen.get_parameters() or []):
                        if param == "443" or param.find(":443") or param == "ssl":
                            server = srv
                    if server:
                        break
                if server:
                    break
            if not server:
                server = servers[0]
        server = trans_(server, Server)
        if not server:
            raise ValueError("no server directive found in main config")

        config.directives.remove(server)
        config.directives.insert(0, server)
        return server

    @dataclass
    class FFOp:  # 查找第一个指令
        directive: str = ""
        parameter: str = ""
        offset: int = 0

    class FLOp(FFOp):  # 查找最后一个指令
        pass

    # 在sever块中查找指令
    @classmethod
    def _find_idx(cls, _block: Union[Block, Http, Config, Upstream], *ops: Union[FFOp, FLOp], default: int = -1):
        directives = _block.get_directives()
        for op in ops:
            target_idx = -1
            for i, directive in enumerate(directives):
                if op.directive and op.directive == directive.get_name() and (
                        op.parameter == "" or any(op.parameter in p for p in directive.get_parameters())
                ):
                    target_idx = i
                    if type(op) is cls.FFOp:
                        return target_idx + op.offset

            if target_idx >= 0:
                return target_idx + op.offset
        return default

    def set_ssl_and_ext(self, site: Union[_PHPSite, _ProxySite, _StaticSite]):
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
            self.bt_conf.include_files[file_path] = ext_conf
            idx = self._find_idx(
                srv_block,
                self.FFOp("root", offset=1), self.FFOp("server_name", offset=1), self.FFOp("listen", offset=1),
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
                    self.FLOp("include", offset=1, parameter="/www/server/panel/vhost"),
                    self.FFOp("root", offset=1), self.FFOp("server_name", offset=1), self.FFOp("listen", offset=1),
                    default=-1)
                cert_conf = [  # 只要备注
                    Directive(
                        name="",
                        parameters=[],
                        comment=[
                            "# SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则",
                            "#error_page 404/404.html;"
                        ]
                    ),
                ]
                srv_block.directives = srv_block.directives[:cert_idx] + cert_conf + srv_block.directives[cert_idx:]
        else:
            min_d = None
            min_d_idx = len(srv_block.directives)
            for d in ssl_certificate + ssl_certificate_key:
                idx = srv_block.directives.index(d)
                if min_d_idx > idx:
                    min_d_idx = idx
                    min_d = d
            min_d = trans_(min_d, Directive)
            if "#error_page 404/404.html;" not in min_d.comment:
                min_d.comment += [
                    "# SSL-START SSL相关配置，请勿删除或修改下一行带注释的404规则",
                    "#error_page 404/404.html;"
                ]

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
            self.bt_conf.include_files[ap_conf_file_path] = ap_conf
            idx = self._find_idx(
                srv_block,
                self.FFOp("root", offset=1), self.FFOp("index", offset=1), self.FFOp("server_name", offset=1),
                default=0,
            )
            srv_block.directives = srv_block.directives[:idx] + apply_conf + srv_block.directives[idx:]

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
                        name="if", parameters=["(", "$fastcgi_script_name", "~", "\"^(.+?\.php)(/.+)$\"", ")"],
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

        elif key == "proxy.conf":
            # proxy_set_header Host $http_host;
            # proxy_set_header X-Real-IP $remote_addr;
            # proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            # proxy_set_header X-Forwarded-Proto $scheme;
            proxy_conf = Config(
                file_path=os.path.join(self._tmp_conf_path, "proxy.conf"),
                directives=[
                    Directive(name="proxy_set_header", parameters=["Host", "$http_host"]),
                    Directive(name="proxy_set_header", parameters=["X-Real-IP", "$remote_addr"]),
                    Directive(name="proxy_set_header", parameters=["X-Forwarded-For", "$proxy_add_x_forwarded_for"]),
                    Directive(name="proxy_set_header", parameters=["X-Forwarded-Proto", "$scheme"])
                ]
            )
            self.bt_conf.bt_default_conf[key] = proxy_conf
            return proxy_conf

        raise ValueError("没有找到对应的配置文件")

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
            raise Exception("未找到php-fpm的socket")

        idx = server.block.directives.index(php_loc)
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
        self.bt_conf.include_files[php_other] = php_other_conf
        args_path = "/www/server/panel/vhost/other_php/{}/enable-php-other.conf".format(site.name)
        server.block.directives[idx] = Include(
            name="include",
            include_path=args_path,
            parameters=[args_path],
            configs=[php_other_conf]
        )

        return

    def _set_main_bt_conf(self):
        # proxy.conf
        http = self.bt_conf.mian_conf.find_http()
        has_proxy_conf = any(["proxy.conf" in (i.get_parameters() or []) for i in http.find_directives("include")])
        has_proxy_set_header = len(http.find_directives("proxy_set_header"))
        if not has_proxy_conf and not has_proxy_set_header:
            proxy_conf = self.bt_conf_by_key("proxy.conf")
            self.bt_conf.include_files[proxy_conf.file_path] = proxy_conf
            http.directives.append(
                Include(name="include", include_path="proxy.conf", parameters=["proxy.conf"],configs=[proxy_conf])
            )


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

    def change_include_path(self):
        pass

    def test_nginx(self):
        """
        测试nginx配置文件
        :return:
        """
        nginx_bin = "/www/server/nginx/sbin/nginx"

        vhost_path = "/www/server/panel/vhost"
        def set_link():
            os.rename("/www/server/nginx/conf", "/www/server/nginx/conf.bak")
            os.symlink(self._tmp_path + "/conf", "/www/server/nginx/conf")

            for file in os.listdir(self._tmp_path + "/vhost"):
                os.rename(vhost_path + "/" + file, vhost_path + "/" + file + ".bak")
                os.symlink(self._tmp_path + "/vhost/" + file, vhost_path + "/" + file)


        def reset_link():
            if os.path.islink("/www/server/nginx/conf") and os.path.exists("/www/server/nginx/conf.bak"):
                os.remove("/www/server/nginx/conf")
                os.rename("/www/server/nginx/conf.bak", "/www/server/nginx/conf")
            for file in os.listdir(self._tmp_path + "/vhost"):
                target_path = vhost_path + "/" + file
                if os.path.islink(target_path) and os.path.exists(target_path + ".bak"):
                    os.remove(target_path)
                    os.rename(target_path + ".bak", target_path)

        set_link()
        cmd = [nginx_bin, "-t", "-c", "/www/server/nginx/conf/nginx.conf"]
        ret = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if ret.returncode != 0:
            print("nginx配置文件测试失败")
            print(ret.stdout.decode())
            print(ret.stderr.decode())
        else:
            print("nginx配置文件测试成功")
        reset_link()



def bt_nginx_format(main_conf_file: str, tmp_path: str = "./") -> BtNginxConf:
    f = _Formatter(main_conf_file, tmp_path)
    ret = f.to_bt_config()
    ret.save_conf()
    f.test_nginx()
    return ret
