import re
from typing import Iterable
from copy import deepcopy


from .utils import _IndexBlockTools
from .location import LocationTools
from itertools import product
from .. import *


class ServerTools(_IndexBlockTools):

    def __init__(self, server: Server):
        super().__init__()
        self._server = server
        self._block: Block = server.get_block()

    def add_domain(self, domain: str, port: str = "", ipv6: bool = False, ssl=False, http3=False):
        # 查找或创建 server_name 指令
        sn_list = self._block.find_directives("server_name")
        if sn_list:
            sn = sn_list[0]
            if domain not in sn.get_parameters():
                sn.get_parameters().append(domain)
        else:
            sn = Directive(name="server_name", parameters=[domain])
            idx = self.find_index(self.OpL("http2"), self.OpR("listen"))
            if idx >= 0:
                self.insert_after(idx, sn)
            else:
                self.insert_after(0, sn)
        if not port:
            return
        # listen
        listen_list = self._server.get_block().find_directives("listen")
        if not any(port in l.get_parameters() for l in listen_list):
            param = [port]
            if ssl:
                param.append("ssl")
            listens = [Directive(name="listen", parameters=param)]
            if ipv6:
                param = ["[::]:{}".format(port)]
                if ssl:
                    param.append("ssl")
                listens.append(Directive(name="listen", parameters=param, inline_comment=["# ipv6"]))

            if http3:
                new_list = []
                for listen in listens:
                    l = deepcopy(listen)
                    l.parameters[1] = "quic"
                    new_list.append(l)
                listens.extend(new_list)

            idx = self.find_index(self.OpR("listen", +1), self.OpL("http2", -1), self.OpL("server_name", -1))
            idx = max(0, idx)
            self.insert_after(idx, *listens)

    def set_ssl_port(self, port: str, is_http3:bool=False, is_http2on:bool=False, is_ipv6:bool=False):
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

    def set_ssl(self, cert: str, key: str, protocols: Iterable[str] = ("TLSv1", "TLSv1.1", "TLSv1.2", "TLSv1.3"),
                http3_header: str = ('quic=":443"; h3=":443"; h3-29=":443"; h3-27=":443";h3-25=":443";'
                                     ' h3-T050=":443"; h3-Q050=":443";h3-Q049=":443";h3-Q048=":443"; '
                                     'h3-Q046=":443"; h3-Q043=":443"')):

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
            print(idx)
            self.insert_after(max(idx, 0), *dir_list)

        idx = self.find_index(self.OpL("ssl_certificate_key", +1))
        ssl_protocols = self._server.top_find_directives("ssl_protocols")
        if len(ssl_protocols) >= 1:
            ssl_protocols[0].parameters = list(protocols)
            for d in ssl_protocols:
                self._block.get_directives().remove(d)
        else:
            self.insert_after(idx, Directive(name="ssl_protocols", parameters=list(protocols)))
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
            now_directives.insert(start_idx, Directive(name="", comment=["#IP-RESTRICT-START 限制访问ip的配置，IP黑白名单"]))
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
        gzip_d =  None
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
        dirs_list: List[Directive]  = []
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

    # is_proxy = True 当需要创建 location 时插入到 #PROXY-CONF-END
    def get_location(self, path: str, modifier: Optional[str] = None, create: bool = True, comment="", is_proxy: bool = True) -> Optional[LocationTools]:
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
                ] +  ops
            idx = self.find_index(*ops)
            self.insert_after(min(max(idx, 0), len(self._block.directives)), l)
            loc = LocationTools(l)

        return loc

    def remove_location(self, path: str, modifier: Optional[str]=None):
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
        if any("PROXY-CONF" in i for i in loc.get_comment()):
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

    def set_log_path(self, access_path: str, error_path: str, uninclude: List[str] = ("bt-monitor.sock", )):
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

    def set_static_cache(self, old_suffix:List[str], new_suffix:List[str], time_out: str) -> Optional[str]:
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


    def remove_static_cache(self, old_suffix:List[str]) -> Optional[str]:
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
