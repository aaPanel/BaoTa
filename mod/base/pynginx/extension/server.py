import re
from typing import Iterable, Union
from copy import deepcopy

from .utils import _IndexBlockTools
from .location import LocationTools
from itertools import product
from .nginx_info import NgInfo, DEFAULT_NGINX
from .. import *


class ServerTools(_IndexBlockTools):

    def __init__(self, server: Server):
        super().__init__()
        self._server = server
        self._block: Block = server.get_block()

    # def add_domain(self, domain: str, port: str = "", ipv6: bool = False, ssl=False, http3=False):
    #     # 查找或创建 server_name 指令
    #     sn_list = self._block.find_directives("server_name")
    #     if sn_list:
    #         sn = sn_list[0]
    #         if domain not in sn.get_parameters():
    #             sn.get_parameters().append(domain)
    #     else:
    #         sn = Directive(name="server_name", parameters=[domain])
    #         idx = self.find_index(self.OpL("http2"), self.OpR("listen"))
    #         if idx >= 0:
    #             self.insert_after(idx, sn)
    #         else:
    #             self.insert_after(0, sn)
    #     if not port:
    #         return
    #     # listen
    #     listen_list = self._server.get_block().find_directives("listen")
    #     if not any(port in l.get_parameters() for l in listen_list):
    #         param = [port]
    #         if ssl:
    #             param.append("ssl")
    #         listens = [Directive(name="listen", parameters=param)]
    #         if ipv6:
    #             param = ["[::]:{}".format(port)]
    #             if ssl:
    #                 param.append("ssl")
    #             listens.append(Directive(name="listen", parameters=param, inline_comment=["# ipv6"]))
    #
    #         if http3:
    #             new_list = []
    #             for listen in listens:
    #                 l = deepcopy(listen)
    #                 l.parameters[1] = "quic"
    #                 new_list.append(l)
    #             listens.extend(new_list)
    #
    #         idx = self.find_index(self.OpR("listen", +1), self.OpL("http2", -1), self.OpL("server_name", -1))
    #         idx = max(0, idx)
    #         self.insert_after(idx, *listens)
    #

    def set_ssl_port(self, port: str, is_http3:bool=False, is_http2on:bool=False,
                     is_ipv6:bool=False):
        self._block.directives = [
            d for d in self._block.directives
            if not (d.get_name() == "listen" and any(p in ("ssl", "quic") for p in d.get_parameters()))
        ]

        add_dirs: List[Directive] = [Directive(name="listen", parameters=[port, "ssl"])]
        if is_ipv6:
            add_dirs.append(Directive(name="listen", parameters=["[::]:{}".format(port), "ssl"]))

        if not is_http2on: # 不能支持 http2 on 的写法时, 改为 listen xx ssl http2;
            for d in add_dirs:
                d.parameters.append("http2")

        if is_http3:
            add_dirs.append(Directive(name="listen", parameters=[port, "quic"]))
            add_dirs.append(Directive(name="listen", parameters=["[::]:{}".format(port), "quic"]))

        if is_http2on:
            self._block.directives = [d for d in self._block.directives if d.get_name() != "http2"]
            add_dirs.append(Directive(name="http2", parameters=["on"]))
        if is_http3:
            self._block.directives = [d for d in self._block.directives if d.get_name() != "http3"]
            add_dirs.append(Directive(name="http3", parameters=["on"]))

        idx = self.find_index(self.OpR("listen", +1), self.OpL("server_name"))
        self.insert_after(max(idx, 0), *add_dirs)

    def remove_domain(self, domain: str, port: str = ""):
        # 移除server_name中的domain
        sn_list = self._block.find_directives("server_name")
        for sn in sn_list:
            if domain in sn.get_parameters():
                sn.get_parameters().remove(domain)

        # listen
        if not port:
            return
        listen_list = self._server.get_block().find_directives("listen")
        for l in listen_list:
            if port in l.get_parameters():
                self._server.get_block().directives.remove(l)

    def set_index(self, index_list: List[str]):
        # 只保留一条index指令
        idxs = self._server.top_find_directives("index")
        if len(idxs) >= 1:
            for idx in idxs[1:]:
                self._block.directives.remove(idx)
            index = trans_(idxs[0], Directive)
            index.parameters = index_list
            return

        index = Directive(name="index", parameters=index_list)
        idx = self.find_index(self.OpL("server_name", +1), self.OpL("root", -1), self.OpR("listen", +1))
        idx = max(idx, 0)
        self.insert_after(idx, index)

    def _set_ssl(self, cert: str, key: str,
                 http3_header: str = ('quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443";'
                                      ' h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; '
                                      'h3-Q046=":443"; h3-Q043=":443"'),
                 ng_info: NgInfo = DEFAULT_NGINX):

        # 只保障一组ssl_certificate/ssl_certificate_key/ssl_protocols
        idx = self.find_index(self.OpL("ssl_certificate"))
        if idx >= 0:  # 存在, 则修改证书配置
            ssl_certificate = trans_(self._server.top_find_directives("ssl_certificate")[0], Directive)
            ssl_certificate.parameters = [cert]
            ssl_certificate_keys = self._server.top_find_directives("ssl_certificate_key")
            if len(ssl_certificate_keys) > 0:
                trans_(ssl_certificate_keys[0], Directive).parameters = [key]
            else:
                self.insert_after(idx, Directive(name="ssl_certificate_key", parameters=[key]))
        else:
            dir_list = [
                Directive(name="ssl_certificate", parameters=[cert]),
                Directive(name="ssl_certificate_key", parameters=[key]),
            ]
            idx = self.find_index(
                self.OpL("", comment="#error_page 404/404.html;"),
                self.OpL("include", +1, parameter="nginx/well-known"),
                self.OpL("root", +1),
                self.OpL("index", +1),
                self.OpL("server_name", +1),
            )
            self.insert_after(max(idx, 0), *dir_list)

        idx = self.find_index(self.OpL("ssl_certificate_key", +1))
        ssl_protocols = self._server.top_find_directives("ssl_protocols")
        if len(ssl_protocols) >= 1:
            trans_(ssl_protocols[0], Directive).parameters = list(ng_info.tls_versions())
            for d in ssl_protocols[1:]:
                self._block.get_directives().remove(d)
        else:
            self.insert_after(idx, Directive(name="ssl_protocols", parameters=ng_info.tls_versions()))
            idx += 1

        default = [
            ("ssl_ciphers", '',
             ["EECDH+CHACHA20:EECDH+CHACHA20-draft:EECDH+AES128:RSA+AES128:EECDH+AES256:RSA+AES256:EECDH+3DES:RSA+3DES:!MD5"]),
            ("ssl_prefer_server_ciphers", '', ["on"]),
            ("ssl_session_cache", '', ["shared:SSL:10m"]),
            ("ssl_session_timeout", '', ["10m"]),
            ("add_header", "Strict-Transport-Security", ["Strict-Transport-Security", "\"max-age=31536000\""]),
            ("error_page", "497", ["497", "https://$host$request_uri"]),
        ]
        if ng_info.http3_enabled():
            default = default + [
                ("quic_retry", '', ["on"]),
                ("quic_gso", '', ["on"]),
                ("ssl_early_data", '', ["on"]),
            ]
            if http3_header:
                default.append(("add_header", "Alt-Svc", ["Alt-Svc", http3_header]))
        add_directives = []
        for d, dp, param in default:
            if dp:
                tmp_dirs = self._server.top_find_directives_with_param(d, dp)
            else:
                tmp_dirs = self._server.top_find_directives_with_param(d)
            if not tmp_dirs:
                add_directives.append(Directive(name=d, parameters=param))

        self.insert_after(idx, *add_directives)

    def _remove_ssl(self):
        ssl_directives = (
            ("ssl_certificate",), ("ssl_certificate_key",),
            ("ssl_protocols",), ("ssl_ciphers",),
            ("ssl_prefer_server_ciphers",), ("ssl_session_tickets",),
            ("ssl_session_cache",), ("ssl_session_timeout",),
            ("add_header", "Strict-Transport-Security"), ("add_header", "Alt-Svc"),
            ("quic_retry",), ("quic_gso",),
            ("ssl_early_data",), ("error_page", "497"),
        )
        new_directives: List[Directive] = []
        for d in self._block.directives:
            if d.get_name() == "ssl_certificate":
                if d.get_comment() == "#error_page 404/404.html;":
                    new_directives.append(Directive(comment=["#error_page 404/404.html;"]))
                continue
            for d_name, *d_param in ssl_directives:
                if d.get_name() == d_name:
                    if d_param:
                        if d.get_parameters() == d_param:
                            break
                    else:
                        break
            else:
                new_directives.append(d)

        has_tip = False
        for idx in range(len(new_directives), -1, -1):
            if "#error_page 404/404.html;" in new_directives[idx].comment:
                if has_tip:
                    new_directives[idx].comment.remove("#error_page 404/404.html;")
                    has_tip = True

        if not has_tip:
            idx = self.find_index(
                self.OpL("include", +1, parameter="nginx/well-known"),
                self.OpL("root", +1),
                self.OpL("index", +1),
                self.OpL("server_name", +1),
            )
            self.insert_after(max(idx, 0), Directive(comment=["#error_page 404/404.html;"])),

        self._block.directives = new_directives


    def _set_ports(self, ports: List[int], has_ssl=False, ng_info=DEFAULT_NGINX):
        ports = list(set([int(i) for i in ports]))
        is_default_server = False
        new_directives = []

        for di in self._block.directives:
            if di.get_name() != "listen":
                if di.get_name() in ("http2", "http3"):
                    continue  # 跟随443端口一起处理
                new_directives.append(di)
                continue  # 跳过非listen指令
            if len(di.get_parameters()) == 0:
                continue  # 无参数的listen直接删除
            addr, other_parms = di.get_parameters()[0], di.get_parameters()[1:]
            if addr.startswith("unix:"):
                new_directives.append(di)
                continue  # unix socket 监听不处理

            if "default_server" in other_parms:
                is_default_server = True
            if "[" in addr and "]" in addr:
                port_str = addr[addr.find("]") + 1:].rsplit(":", 1)[-1]
            else:
                if ":" in addr:
                    port_str = addr.rsplit(":", 1)[1]
                else:
                    port_str = "80"
            try:
                port = int(port_str)
            except:
                continue  # 无法解析的端口不处理

            if port == 443:
                continue  # 443 端口额外处理，如果没有使用ssl，则不需要设置

            if port not in ports:
                continue  # 端口不在列表中的删除
            else:
                ports.remove(port)

            new_directives.append(di)

        self._block.directives = new_directives

        add_list = []
        other_parms: List[str] = []
        if is_default_server:
            other_parms.append("default_server")

        for port in ports:
            if port == 443:  # 443 端口额外处理，如果没有使用ssl，则不需要设置
                continue
            add_list.append(Directive(name="listen", parameters=[str(port), *other_parms]))
            if ng_info.listen_ipv6():
                add_list.append(Directive(name="listen", parameters=["[::]:" + str(port), *other_parms]))

        if has_ssl:
            if ng_info.listen_http2_enabled():
                add_list.append(Directive(name="listen", parameters=["443", "ssl", "http2", *other_parms]))
            else:
                add_list.append(Directive(name="listen", parameters=["443", "ssl", *other_parms]))
            if ng_info.listen_ipv6():
                if ng_info.listen_http2_enabled():
                    add_list.append(Directive(name="listen", parameters=["[::]:443", "ssl", "http2", *other_parms]))
                else:
                    add_list.append(Directive(name="listen", parameters=["[::]:443", "ssl", *other_parms]))

            if ng_info.http3_enabled():
                add_list.append(Directive(name="listen", parameters=["443", "quic", *other_parms]))
                if ng_info.listen_ipv6():
                    add_list.append(Directive(name="listen", parameters=["[::]:443", "ssl", "quic", *other_parms]))

            if ng_info.http2_on_enabled():
                add_list.append(Directive(name="http2", parameters=["on"]))
            if ng_info.http3_enabled():
                add_list.append(Directive(name="http3", parameters=["on"]))

        self.insert(max(self.find_index(self.OpL("server_name")), 0), *add_list)

    def modify_server_config(
            self, domains: List[str] = None, ports: List[int] = None, root_path: str = None,
            ssl_cert: str = None, ssl_key: str = None, ng_info: Union[NgInfo, str] = None,
            http2https: bool=None,
    ):

        ng_info = ng_info or DEFAULT_NGINX
        if isinstance(ng_info, str):
            try:
                ng_info = NgInfo(ng_info)
            except Exception:
                ng_info = DEFAULT_NGINX
        if ng_info.version is None:
            raise ValueError("Nginx binary path cannot be determined")

        if bool(ssl_cert) != bool(ssl_key):
            raise ValueError("ssl_cert and ssl_key must be both set or both unset")

        has_ssl = False
        if self._server.top_find_directives("ssl_certificate") and self._server.top_find_directives(
                "ssl_certificate_key"):
            has_ssl = True

        if ssl_cert == ssl_key == "":
            has_ssl = False
        elif isinstance(ssl_cert, str) and isinstance(ssl_key, str) and ssl_cert and ssl_key:
            has_ssl = True

        # 处理域名
        if domains:
            domains = list(set(domains))
            server_names = self._server.top_find_directives("server_name")
            for sn in server_names[1:]:
                self._block.directives.remove(sn)
            server_name = trans_(server_names[0], Directive)
            server_name.parameters = domains

        # 处理端口
        if ports:
            self._set_ports(ports, has_ssl=has_ssl, ng_info=ng_info)

        if root_path:
            roots = self._server.top_find_directives("root")
            if len(roots) == 0:
                idx = self.find_index(
                    self.OpL("index", +1),
                    self.OpL("include", 0),
                    self.OpL("server_name", +1),
                )
                self.insert(max(idx, 0), Directive(name="root", parameters=[root_path]))
            else:
                for root in roots[1:]:
                    self._block.directives.remove(root)
                r = trans_(roots[0], Directive)
                r.parameters = [root_path]

        if ssl_cert and ssl_key:
            self._set_ssl(ssl_cert, ssl_key, ng_info=ng_info)
        if ssl_cert == "" and ssl_key == "":
            self._remove_ssl()

        if has_ssl:
            http2https = ng_info.default_http2https() if http2https is None else http2https
            self.set_http2https(http2https)

    def set_php_info(self, php_version: str):
        # 先移除原有PHP-INFO块
        includes = self._server.top_find_directives_with_param("include")
        for inc in includes:
            parameters = inc.get_parameters()
            if len(parameters) == 1 and parameters[0].startswith("enable-php-"):
                trans_(inc, Include).parameters[0] = "enable-php-" + php_version + ".conf"

        idx = self.find_index(
            self.OpL("deny", -1),
            self.OpR("include", +1, parameter="vhost/nginx/redirect"),
            self.OpL("include", +1, parameter="nginx/well-known"),
            self.OpL("root", +1),
            self.OpL("server_name", +1),
        )
        self.insert_after(
            (max(idx, 0)),
            Include(
                name="include",
                parameters=["enable-php-" + php_version + ".conf"],
                include_path="enable-php-" + php_version + ".conf",
                comment=["#PHP-INFO  PHP引用配置，可以注释或修改"]
            )
        )

    def set_ip_restrict(self, deny_ips: List[str] = None, allow_ips: List[str] = None):
        # 清除已有allow/deny
        block = self._server.get_block()
        start_idx = 0
        now_directives = []
        for idx, d in enumerate(block.directives):
            if d.get_name() in ("allow", "deny"):
                if start_idx == 0:
                    start_idx = idx
            else:
                now_directives.append(d)
        if start_idx:
            now_directives.insert(start_idx,
                                  Directive(name="", comment=["#IP-RESTRICT-START 限制访问ip的配置，IP黑白名单"]))
        block.directives = now_directives
        if not deny_ips and not allow_ips:
            return
        # 添加新的
        add_dirs: List[Directive] = []
        for ip in deny_ips or []:
            add_dirs.append(Directive(name="deny", parameters=[ip]))
        for ip in allow_ips or []:
            add_dirs.append(Directive(name="allow", parameters=[ip]))
        if len(allow_ips or []) > 0:
            add_dirs.append(Directive(name="deny", parameters=["all"]))

        idx = self.find_index(
            self.OpL(comment="IP-RESTRICT-START", offset=+1),
            self.OpL(comment="IP-RESTRICT-END"),
            self.OpL("include", +1, "enable-php"),  # 放到php配置的后面
            self.OpL("location", -1),  # 放到location的前面
            self.OpL("server_name", +1),
        )
        self.insert_after(max(0, idx), *add_dirs)

    def add_basic_auth(self, path: str, pass_file: str):
        # 匹配已有location，没有则新建
        locations = self._server.top_find_directives("location")
        loc: Optional[Location] = None
        for l in locations:
            l_obj = trans_(l, Location)
            if not l_obj:
                continue
            if l_obj and (l_obj.match == path):
                loc = l_obj
                break
        if not loc:
            loc = Location(name="location", parameters=[path], block=Block(), _parent=self._server, match=path)
            idx = self.find_index(
                self.OpL(comment="#BASICAUTH START", offset=+1),
                self.OpL(comment="#BASICAUTH END"),
                self.OpL("server_name", +1),
            )
            self.insert_after(min(max(0, idx), len(self._block.directives)), loc)

        add_dirs = []
        tmp_list = loc.top_find_directives("auth_basic")
        if tmp_list:
            for tmp in tmp_list[1:]:
                tmp.get_block().get_directives().remove(tmp)
            trans_(tmp_list[0], Directive).parameters = ['"Authorization"']
        else:
            add_dirs.append(Directive(name="auth_basic", parameters=['"Authorization"']))

        tmp_list = loc.top_find_directives("auth_basic_user_file")
        if tmp_list:
            for tmp in tmp_list[1:]:
                tmp.get_block().get_directives().remove(tmp)
            trans_(tmp_list[0], Directive).parameters = [pass_file]
        else:
            add_dirs.append(Directive(name="auth_basic_user_file", parameters=[pass_file]))

        if add_dirs:
            loc.block.directives = add_dirs + loc.block.directives

    def remove_basic_auth(self, path: str):
        locations = self._server.top_find_directives("location")
        loc: Optional[Location] = None
        for l in locations:
            l_obj = trans_(l, Location)
            if not l_obj:
                continue
            if l_obj and (l_obj.match == path):
                loc = l_obj
                break
        if not loc:
            return

        loc.block.directives = [d for d in loc.block.directives if not d.get_name().startswith("auth_basic")]
        if loc.block.get_directives():  # 如果已经没有其他配置了，则删除location
            return

        if loc.comment:
            for idx, d in enumerate(self._block.directives):
                if d is loc:
                    self._block.directives[idx] = Directive(name="", comment=loc.comment)

    def set_gzip(self, status: bool, level: int, min_size: str, gz_type: List[str]):
        # 先移除原有gzip相关指令
        block = self._server.get_block()
        gzip_d = None
        for d in block.directives:
            if d.get_name() == "gzip":
                gzip_d = d
        if gzip_d:
            gzip_d = trans_(gzip_d, Directive)
            gzip_d.name = ""
            gzip_d.parameters = []

        gzip_names = [
            "gzip_min_length", "gzip_buffers", "gzip_http_version", "gzip_comp_level",
            "gzip_types", "gzip_vary", "gzip_proxied", "gzip_disable"
        ]
        block.directives = [d for d in block.directives if d.get_name() not in gzip_names]
        if not status:
            return
        # 添加一组gzip配置
        add_dirs = [
            Directive(name="gzip", parameters=["on"], inline_comment=["#GZIP 配置传输压缩"]),
            Directive(name="gzip_min_length", parameters=[min_size], inline_comment=["#GZIP 配置传输最小长度"]),
            Directive(name="gzip_buffers", parameters=["16 8k"], inline_comment=["#GZIP 配置传输缓存块"]),
            Directive(name="gzip_http_version", parameters=["1.1"], inline_comment=["#GZIP 配置传输协议版本"]),
            Directive(name="gzip_comp_level", parameters=[str(level)], inline_comment=["#GZIP 配置传输压缩级别"]),
            Directive(name="gzip_types", parameters=gz_type),
            Directive(name="gzip_vary", parameters=["on"]),
            Directive(name="gzip_proxied", parameters=["expired", "no-cache", "no-store", "private", "auth"]),
            Directive(name="gzip_disable", parameters=['"MSIE [1-6]\\."'],
                      inline_comment=["#GZIP 拒绝过低版本浏览器压缩"]),
        ]

        idx = self.find_index(
            self.OpL(comment="GZIP START", offset=+1),
            self.OpL(comment="GZIP END"),
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
            self.OpL("include", +1, "enable-php"),  # 放到php配置的后面
            self.OpL("location", -1),  # 放到location的前面
            self.OpL("server_name", +1),
        )
        self.insert_after(max(0, idx), *add_dirs)

    def set_http2https(self, status: bool = True):
        directives = self._block.directives
        start_idx = -1
        qu = [("set", "$isRedcert"), ("if", "$server_port"), ("if", "$uri", "well-known"), ("if", "$isRedcert")]
        dir_list = []
        for idx, d in enumerate(directives):
            now_dir, now_parms = qu[0][0], qu[0][1:]
            parameters = d.get_parameters()
            if d.get_name() == now_dir and all([any([np in p for p in parameters]) for np in now_parms]):
                dir_list.append(d)
                start_idx = idx if start_idx == -1 else start_idx
                qu = qu[1:]
                if len(qu) == 0:
                    break

        if dir_list:  # 删除已经存在的配置
            for d in dir_list:
                directives.remove(d)

        if not status:
            return

        add_dirs = [
            Directive(name="set", parameters=["$isRedcert", "1"], comment=["# HTTP_TO_HTTPS_START 配置强制https请求"]),
            Directive(name="if", parameters=["(", "$server_port", "!=", "443", ")"], block=Block(
                directives=[Directive(name="set", parameters=["$isRedcert", "2"])])),
            Directive(name="if", parameters=["(", "$uri", "~", r"/\.well-known/", ")"], block=Block(
                directives=[Directive(name="set", parameters=["$isRedcert", "1"])])),
            Directive(name="if", parameters=["(", "$isRedcert", "!=", "1", ")"], block=Block(
                directives=[Directive(name="rewrite", parameters=["^(.*)$", "https://$host$1", "permanent"])])),
        ]

        idx = self.find_index(self.OpL("ssl_certificate", -1), self.OpL("server_name", +1))
        self.insert_after(max(0, idx), *add_dirs)

    def set_server_proxy_cache(self, status: bool, cache_name: str, cache_time: str = "1d"):
        """设置server块级别的代理缓存"""
        directives = self._block.directives
        dir_list = []
        other_queue = (("proxy_cache_valid",), ("proxy_cache_valid",), ("location", r".*\.("))
        find_other = False
        start_dix = 0
        for idx, sub_d in enumerate(directives):
            if sub_d.get_name() == "proxy_cache":
                if idx < len(directives) - 3 and \
                        directives[idx + 1].get_name() == "proxy_cache_key" and \
                        directives[idx + 2].get_name() == "proxy_ignore_headers":
                    dir_list = [sub_d, directives[idx + 1], directives[idx + 2]]
                    start_dix = idx
                    find_other = True
            if find_other:
                now_dir, now_parms = other_queue[0][0], other_queue[0][1:]
                parameters = sub_d.get_parameters()
                if sub_d.get_name() == now_dir and all([any([np in p for p in parameters]) for np in now_parms]):
                    dir_list.append(sub_d)
                    other_queue = other_queue[1:]
                    if len(other_queue) == 0:
                        break

        if len(dir_list) > 0:
            for d in dir_list:
                directives.remove(d)
            # 保留配置注释
            directives.insert(start_dix, Directive(name="", comment=dir_list[0].get_comment()))

        if not status:
            return False

        add_dirs = [
            Directive(name="proxy_cache", parameters=[cache_name], inline_comment=["# 代理缓存配置"]),
            Directive(name="proxy_cache_key", parameters=["$host$uri$is_args$args"]),
            Directive(name="proxy_ignore_headers",
                      parameters=["Set-Cookie", "Cache-Control", "expires", "X-Accel-Expires"]),
            Directive(name="proxy_cache_valid", parameters=["200", "304", "301", "302", cache_time]),
            Directive(name="proxy_cache_valid", parameters=["404", "1m"]),
            Directive(name="location",
                      parameters=["~", r".*\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"],
                      block=Block(directives=[
                          Directive(name="expires", parameters=[cache_time]),
                          Directive(name="error_log", parameters=["/dev/null"]),
                          Directive(name="access_log", parameters=["/dev/null"]),
                      ]))
        ]

        idx = self.find_index(
            self.OpL(comment="GLOBAL-CACHE START", offset=+1),
            self.OpL(comment="GLOBAL-CACHE END"),
            self.OpL("gzip_disable", +1),  # 放到gzip配置的后面
            self.OpR("sub_filter", +1),  # 放到sub_filter配置的后面
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
            self.OpL("include", +1, "enable-php"),  # 放到php配置的后面
            self.OpL("location", -1),  # 放到location的前面
            self.OpL("server_name", +1),
        )
        self.insert_after(max(0, idx), *add_dirs)

    def set_websocket_support(self, status: bool = True):
        default = (
            ("proxy_http_version", "", ["1.1"]),
            ("proxy_set_header", "Upgrade", ["Upgrade", "$http_upgrade"]),
            ("proxy_set_header", "Connection", ["Connection", "$connection_upgrade"]),
        )
        add_dirs: List[Directive] = []
        dirs_list: List[Directive] = []
        for name, param, param_vals in default:
            if param:
                tmp_dirs = self._server.top_find_directives_with_param(name, param)
            else:
                tmp_dirs = self._server.top_find_directives_with_param(name)

            if tmp_dirs:
                dirs_list.extend(tmp_dirs)

            add_dirs.append(Directive(name=name, parameters=param_vals))

        if len(dirs_list) > 0:
            start_d = None
            start_idx = 0
            for d in dirs_list:
                if any("WEBSOCKET-SUPPORT" in i for i in d.get_comment()):
                    start_d = d
                    start_idx = self._block.directives.index(d)
                self._block.directives.remove(d)

            if start_d:
                self._block.directives.insert(start_idx, Directive(name="", comment=start_d.get_comment()))

        if not status:
            return

        else:
            add_dirs[0].inline_comment = ["# 支持websocket链接"]
            idx = self.find_index(
                self.OpL(comment="WEBSOCKET-SUPPORT START", offset=+1),
                self.OpL(comment="WEBSOCKET-SUPPORT END"),
                self.OpL("location", +1, r".*\.(css|js"),  # 放到全局PROXY_CACHE后面
                self.OpL("gzip_disable", +1),  # 放到gzip配置的后面
                self.OpR("sub_filter", +1),  # 放到sub_filter配置的后面
                self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
                self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
                self.OpL("include", +1, "enable-php"),  # 放到php配置的后面
                self.OpL("location", ),  # 放到location的前面
                self.OpL("server_name", +1),
            )
            self.insert_after(max(idx, 0), *add_dirs)

    # create 为True时，需要传入 path和modifier，此时会尝试创建一个空的location，并返回
    # sub_directives 检查匹配的location中是否包含全部的这些指定指令，可以传递多个指令，指令可以为列表，此时[0]=>匹配指令，[:1]=>匹配参数
    def get_location(self,
                     path: Optional[str] = None,
                     modifier: Optional[str] = None,
                     create: bool = False,
                     sub_directives: Optional[List[Union[str, List[str]]]] = None
                     ) -> List[Location]:
        tmp_locations = self._server.top_find_directives("location")
        locs: List[Location] = []
        for loc_if in tmp_locations:
            loc_obj = trans_(loc_if, Location)
            if not loc_obj:
                continue
            if path and loc_obj.match != path:
                continue
            if modifier is not None and loc_obj.modifier != modifier:
                continue
            if sub_directives:
                matched = True
                for sub_directive in sub_directives:
                    if isinstance(sub_directive, str):
                        if not loc_obj.top_find_directives_with_param(sub_directive):
                            matched = False
                            break
                    elif isinstance(sub_directive, (list, tuple, Iterable)) and len(sub_directive) >= 1:
                        if not loc_obj.top_find_directives_with_param(sub_directive[0], *sub_directive[1:]):
                            matched = False
                            break
                if not matched:
                    continue
            locs.append(loc_obj)

        if locs:
            return locs

        if create and (not path):
            raise ValueError("创建时请指定path")

        if create:
            modifier = "" if modifier is None else modifier
            l = Location(
                name="location",
                comment=list(),
                parameters=[path] if not modifier else [modifier, path],
                block=Block(directives=[]),
                _parent=self._server,
                modifier=modifier,
                match=path
            )
            ops = [
                self.OpL(comment="HTTP反向代理相关配置开始", offset=+1),
                self.OpL(comment="PROXY-CONF-START", offset=+1),
                self.OpL("location", +1),
                self.OpL("server_name", +1),
            ]
            idx = self.find_index(*ops)
            self.insert_after(min(max(idx, 0), len(self._block.directives)), l)
            locs.append(l)

        return locs

    # is_proxy = True 当需要创建 location 时插入到 #PROXY-CONF-END
    def get_proxy_location(self, path: str, modifier: Optional[str] = None, create: bool = True, comment="",
                           is_proxy: bool = True) -> Optional[LocationTools]:
        tmp_locations = self._server.top_find_directives("location")
        loc: Optional[LocationTools] = None
        for loc_if in tmp_locations:
            loc_obj = trans_(loc_if, Location)
            if not loc_obj:
                continue
            if loc_obj.match == path and (modifier is None or modifier == loc_obj.modifier):
                loc = LocationTools(loc_obj)
                break
        if create and not loc:
            l = Location(
                name="location",
                comment=[comment] if comment else list(),
                parameters=[path] if not modifier else [modifier, path],
                block=Block(directives=[]),
                _parent=self._server,
                modifier=modifier,
                match=path
            )
            ops = [
                self.OpL("location", +1),
                self.OpL("server_name", +1),
            ]
            if is_proxy:
                ops = [
                          self.OpL(comment="PROXY-CONF-END"),
                          self.OpL(comment="PROXY-CONF-START", offset=+1),
                      ] + ops
            idx = self.find_index(*ops)
            self.insert_after(min(max(idx, 0), len(self._block.directives)), l)
            loc = LocationTools(l)

        return loc

    def remove_location(self, path: str, modifier: Optional[str] = None,
                        hold_comments:Iterable[str] = ("PROXY-CONF", "HTTP反向代理") ):
        tmp_locations = self._server.top_find_directives("location")
        loc: Optional[Location] = None
        for loc_if in tmp_locations:
            loc_obj = trans_(loc_if, Location)
            if not loc_obj:
                continue
            if loc_obj.match == path and (modifier == loc_obj.modifier or modifier is None):
                loc = loc_obj
                break

        idx = self._block.directives.index(loc)
        if any(any(c in i for c in hold_comments) for i in loc.get_comment()):
            self._block.directives.remove(loc)
            self._block.directives.insert(idx, Directive(name="", comment=loc.get_comment()))
        else:
            self._block.directives.remove(loc)

    def set_security_referer(
            self,
            status: bool = True,
            suffix_list: List[str] = None,
            domain_list: List[str] = None,
            return_rule: str = "404",
            allow_empty: bool = False):
        loc: Optional[Location] = None
        locs = self._server.top_find_directives_with_param("location", "~")
        if locs:
            for loc_if in locs:
                loc_obj = trans_(loc_if, Location)
                if not loc_obj:
                    continue
                if not loc_obj.match.startswith(r".*\.(") and not loc_obj.match.endswith(r")$"):
                    continue
                if loc_obj.top_find_directives("expires") and \
                        loc_obj.top_find_directives("valid_referers") and \
                        loc_obj.top_find_directives_like_param("if", "$invalid_refere"):
                    loc = loc_obj
                    break
        if not status:
            if loc:
                loc.block.directives = [
                    sub_d for sub_d in loc.block.directives
                    if not sub_d.get_name() in ("expires", "valid_referers", "if", "access_log")
                ]
                if not loc.block.directives:
                    self._block.directives.remove(loc)
            return

        if not domain_list or not suffix_list:
            raise ValueError("suffix_list or domain_list is empty")

        parameter = r".*\.(" + r"|".join([re.escape(s) for s in suffix_list or []]) + r")$"
        valid_args = [] if not allow_empty else ["none", "blocked"]
        if domain_list:
            valid_args.extend(domain_list)
        if return_rule.isdecimal():
            ret = Directive(name="return", parameters=[return_rule])
        else:
            ret = Directive(name="rewrite", parameters=["/.*", return_rule, "break"])
        if not loc:
            loc = Location(
                name="location",
                parameters=["~", parameter],
                block=Block(directives=[
                    Directive(name="expires", parameters=["1d"]),
                    Directive(name="access_log", parameters=["/dev/null"]),
                    Directive(name="valid_referers", parameters=valid_args),
                    Directive(name="if", parameters=["($invalid_referer)"], block=Block(directives=[ret])),
                ]),
            )

            idx = self.find_index(
                self.OpL("include", +1, "nginx/well-known"),  # 放到php配置的后面
                self.OpL("root", +1),  # 放到首位root的后面
                self.OpL("server_name", +1),
            )
            self.insert_after(max(idx, 0), loc)
        else:
            loc.parameters = ["~", parameter]
            loc.modifier, loc.match = "~", parameter
            valid_r = loc.top_find_directives("valid_referers")
            trans_(valid_r[0], Directive).parameters = valid_args

            if_dirs = loc.top_find_directives_like_param("if", "$invalid_referer")
            if_dir = trans_(if_dirs[0], Directive)
            if not if_dir.block:
                if_dir.block = Block(directives=[ret])
            else:
                if_dir.block.directives = [i for i in if_dir.block.directives if
                                           i.get_name() not in ("return", "rewrite")]
                if_dir.block.directives.append(ret)

        return

    def set_log_path(self, access_path: str, error_path: str, uninclude: List[str] = ("bt-monitor.sock",)):
        access_logs = [
            i for i in self._block.directives
            if i.get_name() == "access_log" and not any(unp in p for unp, p in product(uninclude, i.get_parameters()))
        ]
        add_dirs = []
        if access_logs:
            trans_(access_logs[0], Directive).parameters = [access_path]
        else:
            add_dirs.append(
                Directive(name="access_log", parameters=[access_path])
            )
        error_logs = [
            i for i in self._block.directives
            if i.get_name() == "error_log" and not any(unp in p for unp, p in product(uninclude, i.get_parameters()))
        ]
        if error_logs:
            trans_(error_logs[0], Directive).parameters = [error_path]
        else:
            add_dirs.append(
                Directive(name="error_log", parameters=[error_path])
            )

        if add_dirs:
            self._block.directives.extend(add_dirs)

    def set_static_cache(self, old_suffix: List[str], new_suffix: List[str], time_out: str) -> Optional[str]:
        static_pattern = re.compile(r'\.\*\\\.\((?P<suffix>[^)]+)\)\??\$')
        tmp_locations = self._server.top_find_directives_with_param("location", "~", static_pattern)
        new_match = r".*\.({})$".format("|".join([re.escape(s) for s in new_suffix]))
        if old_suffix:
            if tmp_locations:
                target_loc = None
                match_percent = 0
                this_loc = None
                for loc in tmp_locations:
                    loc_obj = trans_(loc, Location)
                    if not loc_obj:
                        continue
                    if not loc_obj.top_find_directives("expires"):
                        continue
                    suffix = static_pattern.match(loc_obj.match).group("suffix").split("|")
                    tmp_match_percent = len(set(suffix) & set(old_suffix)) / len(suffix)
                    if tmp_match_percent > match_percent:
                        target_loc = loc_obj
                        this_loc = loc
                        match_percent = tmp_match_percent
                if target_loc:
                    target_loc.match = new_match
                    target_loc.parameters = ["~", new_match]
                    the_directive = target_loc.top_find_directives("expires")[0]
                    expires = trans_(the_directive, Directive)
                    expires.parameters = [time_out]
                    target_loc.block.replace_directive(the_directive, expires)
                    self._server.block.replace_directive(this_loc, target_loc)
                    # 正常修改成功
                    return None
            # 指定后操作后配置文件被修改了？，无法正常修改， 此时返回异常信息
            return "未匹配到静态缓存配置，无法修改"
        else:
            # 没有指定原后缀
            # tmp_locations = [loc for loc in tmp_locations if loc.top_find_directives("expires")]
            # if len(tmp_locations) >= 2: # 匹配到两个即以上,执行替换第一个，不在允许添加，符合设计
            #     target_loc = trans_(tmp_locations[0], Location)
            #     target_loc.match = new_match
            #     target_loc.parameters[1] = new_match
            #     the_directive = target_loc.top_find_directives("expires")[0]
            #     expires = trans_(the_directive, Directive)
            #     expires.parameters = [time_out]
            #     target_loc.block.replace_directive(the_directive, expires)
            #     self._server.block.replace_directive(tmp_locations[0], target_loc)
            #     return None
            # else:
            new_loc = Location(
                name="location",
                match=new_match,
                parameters=["~", new_match],
                block=Block(directives=[
                    Directive(name="expires", parameters=[time_out]),
                    Directive(name="error_log", parameters=["/dev/null"]),
                    Directive(name="access_log", parameters=["/dev/null"]),
                ]),
            )
            idx = self._server.block.directives.index(tmp_locations[0]) + 1 if tmp_locations else 0
            if not idx:
                idx = self.find_index(
                    self.OpR("access_log"),
                    self.OpR("location", +1),
                    default=len(self._server.block.directives) - 1
                )
            self.insert_after(idx, new_loc)
            return None

    def remove_static_cache(self, old_suffix: List[str]) -> Optional[str]:
        if not old_suffix:
            return "请指定需要删除的静态缓存后缀"
        static_pattern = re.compile(r'\.\*\\\.\((?P<suffix>[^)]+)\)\??\$')
        tmp_locations = self._server.top_find_directives_with_param("location", "~", static_pattern)
        if not tmp_locations:
            return "未匹配到静态缓存配置，无法删除"

        loc_len = 0
        this_loc = None
        for loc in tmp_locations:
            loc_obj = trans_(loc, Location)
            if not loc_obj:
                continue
            if not loc_obj.top_find_directives("expires"):
                continue
            suffix = static_pattern.match(loc_obj.match).group("suffix").split("|")
            tmp_loc_len = len(set(suffix) & set(old_suffix))
            if tmp_loc_len > loc_len:
                this_loc = loc
                loc_len = tmp_loc_len

        if this_loc:
            self._server.block.directives.remove(this_loc)
            return None
        else:
            return "未匹配到静态缓存配置，无法删除"

    def set_stop_status(self, to_stop: bool):
        if to_stop:  # 停止
            loc_list = self._server.top_find_directives_with_param("location", "=", "/bt-stop.html")
            if not loc_list:
                self.insert_after(
                    0,
                    Location(
                        name="location",
                        modifier="=",
                        match="/bt-stop.html",
                        parameters=["=", "/bt-stop.html"],
                        inline_comment=["# 网站停止，并设置网站停止页面"],
                        block=Block(directives=[
                            Directive(name="root", parameters=["/www/server/stop"])
                        ])
                    )
                )

            rewrite_all_list = self._server.top_find_directives_with_param(
                "rewrite", "^/(?!bt-stop\.html$).*", "/bt-stop.html", "last"
            )

            new_rewrite_all = Directive(
                name="rewrite",
                parameters=[
                    "^/(?!bt-stop\.html$).*",
                    "/bt-stop.html",
                    "last"
                ]
            )

            if not rewrite_all_list:
                self.insert_after(0, new_rewrite_all)

            else:
                for tmp in rewrite_all_list:
                    self._block.directives.remove(tmp)
                self.insert_after(0, new_rewrite_all)
        else:  # 关闭
            loc_list = self._server.top_find_directives_with_param("location", "=", "/bt-stop.html")
            if loc_list:
                for tmp in loc_list:
                    self._block.directives.remove(tmp)

            rewrite_all_list = self._server.top_find_directives_with_param(
                "rewrite", "^/(?!bt-stop\.html$).*", "/bt-stop.html", "last"
            )
            if rewrite_all_list:
                for tmp in rewrite_all_list:
                    self._block.directives.remove(tmp)
