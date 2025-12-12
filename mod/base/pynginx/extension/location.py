from typing import Tuple

from .utils import _IndexBlockTools
from .. import *

class LocationTools(_IndexBlockTools):

    def __init__(self, location: Location):
        super().__init__()
        self._block: Block = location.get_block()
        self._location: Location = location

    def add_proxy(self, proxy_pass_data: str, set_host: str = "$http_host", sni_status:bool=False):
        proxy_pass_tmp = self._location.top_find_directives("proxy_pass")
        add_dirs = []
        if proxy_pass_tmp:
            trans_(proxy_pass_tmp[0], Directive).parameters = [proxy_pass_data]
        else:
            add_dirs.append(Directive(name="proxy_pass", parameters=[proxy_pass_data]))

        proxy_host_tmp = self._location.top_find_directives_with_param("proxy_set_header", "Host")
        if proxy_host_tmp:
            trans_(proxy_host_tmp[0], Directive).parameters = ["Host", set_host]
        else:
            add_dirs.append(Directive(name="proxy_set_header", parameters=["Host", set_host]))

        idx = self.find_index(
            self.OpL("auth_basic_user_file", +1),  # 放到location的前面
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
        )
        idx = max(0, idx)
        self.insert_after(max(0, idx), *add_dirs)
        idx = len(add_dirs)

        default_set_header = (
            ("X-Real-IP", "$remote_addr"),
            ("X-Real-Port", "$remote_port"),
            ("X-Forwarded-For", "$proxy_add_x_forwarded_for"),
            ("X-Forwarded-Proto", "$scheme"),
            ("X-Forwarded-Host", "$host"),
            ("X-Forwarded-Port", "$server_port"),
            ("Remote-Host", "$remote_addr"),
        )
        add_dirs: List[Directive] = []
        set_headers = self._location.top_find_directives("proxy_set_header")
        for header, value in default_set_header:
            if not any((header.lower() == d.get_parameters()[0].lower() for d in set_headers if d.get_parameters())):
                add_dirs.append(Directive(name="proxy_set_header", parameters=[header, value]))

        self.insert_after(idx, *add_dirs)
        idx += len(add_dirs)
        sni_d = self._location.top_find_directives("proxy_ssl_server_name")
        if sni_d:
            if sni_status:
                trans_(sni_d[0], Directive).parameters = ["on"]
                for d in sni_d[1:]:
                    self._block.directives.remove(d)
            else:
                for d in sni_d:
                    self._block.directives.remove(d)
        else:
            if sni_status:
                self.insert_after(idx, Directive(name="proxy_ssl_server_name", parameters=["on"]))

    def set_proxy_timeout(self, connect: str, send: str, read: str):
        set_data = (
            ("proxy_connect_timeout", connect if connect.endswith("s") else connect + "s"),
            ("proxy_send_timeout", send if send.endswith("s") else send + "s"),
            ("proxy_read_timeout", read if read.endswith("s") else read + "s"),
        )
        add_dirs = []
        dir_list = []
        for name, value in set_data:
            tmp_dirs = self._location.top_find_directives(name)
            if tmp_dirs and not value:
                dir_list.extend(tmp_dirs)
            elif tmp_dirs and value:
                dir_list.extend(tmp_dirs[1:])
                trans_(tmp_dirs[0], Directive).parameters = [value]
            elif value:
                add_dirs.append(Directive(name=name, parameters=[value]))

        if dir_list:
            for d in dir_list:
                self._block.directives.remove(d)

        if add_dirs:
            idx = self.find_index(self.OpR("proxy_set_header", +1, "Remote-Host"))
            self.insert_after(idx, *add_dirs)

    def set_websocket_support(self, status: bool = True):
        default = (
            ("proxy_http_version", "", ["1.1"]),
            ("proxy_set_header", "Upgrade", ["Upgrade", "$http_upgrade"]),
            ("proxy_set_header", "Connection", ["Connection", "$connection_upgrade"]),
        )
        add_dirs: List[Directive]= []
        dirs_list = []
        for name, param, param_vals in default:
            if param:
                tmp_dirs = self._location.top_find_directives_with_param(name, param)
            else:
                tmp_dirs = self._location.top_find_directives_with_param(name)

            if tmp_dirs:
                dirs_list.extend(tmp_dirs)

            add_dirs.append(Directive(name=name, parameters=param_vals))

        for d in dirs_list:
            self._block.directives.remove(d)

        if not status:
            return
        else:
            if not add_dirs:
                return
            add_dirs[0].comment = ["# 支持websocket链接"]
            idx = self.find_index(
                self.OpL("proxy_read_timeout", +1),  # 放到全局PROXY_CACHE后面
                self.OpL("proxy_set_header", parameter="Accept-Encoding"), # 放到gzip配置的后面
            )
            self.insert_after(max(idx, 0), *add_dirs)

    def set_ip_restrict(self, deny_ips: List[str] = None, allow_ips: List[str] = None):
        # 清除已有allow/deny
        self._block.directives = [d for d in self._block.directives if d.get_name() not in ("allow", "deny")]
        if not deny_ips and not allow_ips:
            return
        # 添加新的
        add_dirs: List[Directive] = []
        for ip in deny_ips or []:
            add_dirs.append(Directive(name="deny", parameters=[ip]))
        for ip in allow_ips or []:
            add_dirs.append(Directive(name="allow",parameters=[ip]))
        if len(allow_ips or []) > 0:
            add_dirs.append(Directive(name="deny", parameters=["all"]))

        add_dirs[0].comment=["# 限制访问ip的配置，IP黑白名单"]
        self.insert_after(0, *add_dirs)

    def add_basic_auth(self, pass_file: str):
        self.remove_basic_auth()
        add_dirs = [
            Directive(name="auth_basic", parameters=['"Authorization"']),
            Directive(name="auth_basic", parameters=[pass_file])
        ]
        idx = self.find_index(
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
        )
        self.insert_after(max(idx, 0), *add_dirs)

    def remove_basic_auth(self):
        self._block.directives = [d for d in self._block.directives if not d.get_name().startswith("auth_basic")]

    def set_sub_filter(self, filters:List[Tuple[str, str, str]], regexp_support: bool = False):
        self._block.directives = [d for d in self._block.directives if not d.get_name() in ("sub_filter", "subs_filter", "sub_filter_once")]
        add_dirs = []
        for old_str, new_str, flag in filters:
            if not regexp_support:
                p = [old_str, new_str]
            else:
                p = [old_str, new_str, flag]
            p = map(lambda x: '""' if x == "" else x, p)
            add_dirs.append(Directive(name="subs_filter" if regexp_support else "sub_filter", parameters=list(p)))

        tmp = self._location.top_find_directives_with_param("proxy_set_header", "Accept-Encoding")
        if tmp:
            trans_(tmp[0], Directive).parameters = ["Accept-Encoding", '""']
        else:
            add_dirs.insert(0, Directive(name="proxy_set_header", parameters=["Accept-Encoding", '""']))

        if not regexp_support:
            tmp = self._location.top_find_directives("sub_filter_once")
            if tmp:
                trans_(tmp[0], Directive).parameters = ["off"]
            else:
                add_dirs.append(Directive(name="sub_filter_once", parameters=["off"]))
        else:
            tmp = self._location.top_find_directives("sub_filter_once")
            if tmp:
                for d in tmp:
                    self._block.directives.remove(d)

        idx = len(self._block.directives)
        self.insert_after(idx, *add_dirs)

    # 旧版本,该版本的配置方式不会正确生效，目前弃用，新版本会调用其方法尝试清空旧的错误配置，并添加新的配置
    def set_proxy_cache_old(self, status: bool, cache_name: str, cache_time: str = "1d"):
        """设置location块级别的代理缓存"""
        directives = self._block.directives
        dir_list = []
        other_queue = (("proxy_cache_valid", ), ("proxy_cache_valid", ), ("location", r".*\.("))
        find_other = False
        for idx, sub_d in enumerate(directives):
            if sub_d.get_name() == "proxy_cache":
                if idx < len(directives) - 3 and \
                        directives[idx+1].get_name() == "proxy_cache_key" and\
                        directives[idx+2].get_name() == "proxy_ignore_headers":
                    dir_list = [sub_d, directives[idx+1], directives[idx+2]]
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

        if not status:
            return False

        add_dirs = [
            Directive(name="proxy_cache", parameters=[cache_name], comment=["# PROXY-CACHE代理缓存配置"]),
            Directive(name="proxy_cache_key", parameters=["$host$uri$is_args$args"]),
            Directive(name="proxy_ignore_headers", parameters=["Set-Cookie", "Cache-Control", "expires", "X-Accel-Expires"]),
            Directive(name="proxy_cache_valid", parameters=["200", "304","301","302", cache_time]),
            Directive(name="proxy_cache_valid", parameters=["404", "1m"]),
            Directive(
                name="location", parameters=["~", r".*\.(css|js|jpe?g|gif|png|webp|woff|eot|ttf|svg|ico|css\.map|js\.map)$"],
                  block=Block(directives=[
                      Directive(name="expires", parameters=[cache_time]),
                      Directive(name="error_log", parameters=["/dev/null"]),
                      Directive(name="access_log", parameters=["/dev/null"]),
                  ])
            )
        ]

        idx = self.find_index(
            self.OpL("proxy_set_header", +1, "Remote-Host"),  # 放到ip黑白名单配置的后面
            self.OpL("proxy_set_header", +1, "Connection"),  # 放到ip黑白名单配置的后面
            self.OpL("gzip"),  # 放到gzip配置的前面
            self.OpL("sub_filter"),  # 放到sub_filter配置的前面
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
        )
        self.insert_after(max(0, idx), *add_dirs)


    def set_proxy_cache(self,
                        status: bool, cache_name: str, cache_time: str = "1d",
                        cache_suffix: str = "css,js,jpe,jpeg,gif,png,webp,woff,eot,ttf,svg,ico,css.map.js.map"):
        self.set_proxy_cache_old(status=False, cache_name="", cache_time="")  # 旧版清除
        proxy_pass = self._location.top_find_directives("proxy_pass")
        if len(proxy_pass) < 0:
            proxy_pass_copy = None
        else:
            pp = trans_(proxy_pass[0], Directive)
            proxy_pass_copy = Directive(name=pp.get_name(), parameters=pp.get_parameters())
        sub_location = self._location.top_find_directives("location")
        target_location = None
        if len(sub_location) > 0:
            for sl in sub_location:
                the_sl = trans_(sl, Location)
                has_proxy_cache = the_sl.top_find_directives("proxy_cache")
                has_proxy_cache_valid = the_sl.top_find_directives("proxy_cache_valid")
                has_proxy_cache_key = the_sl.top_find_directives("proxy_cache_key")
                if len(has_proxy_cache) > 0 or len(has_proxy_cache_valid) > 0 or len(has_proxy_cache_key) > 0:
                    target_location = sl
                    break
        if target_location is not None:
            self._block.directives.remove(target_location)

        if not status:
            return

        parameter2 = r".*\.(" + "|".join([re.escape(i) for i in cache_suffix.split(",")]) + ")$"
        add_loc = Location(
            name="location",
            parameters=["~", parameter2],
            block=Block(directives=[
                Directive(name="proxy_cache", parameters=[cache_name]),
                Directive(name="proxy_cache_key", parameters=["$host$uri$is_args$args"]),
                Directive(name="proxy_ignore_headers", parameters=["Set-Cookie", "Cache-Control", "expires", "X-Accel-Expires"]),
                Directive(name="proxy_cache_valid", parameters=["200", "304","301","302", cache_time]),
                Directive(name="proxy_cache_valid", parameters=["404", "1m"]),
                Directive(name="access_log", parameters=["/dev/null"]),
                Directive(name="error_log", parameters=["/dev/null"]),
            ]),)

        if proxy_pass_copy is not None:
            add_loc.block.directives.insert(0, proxy_pass_copy)

        proxy_cache = self._location.top_find_directives("proxy_cache")
        for pc in proxy_cache:
            self._block.directives.remove(pc)

        add_x_caches = self._location.top_find_directives_with_param("add_header", "X-Cache")
        for ac in add_x_caches:
            self._block.directives.remove(ac)

        add_list = [
            Directive(name="proxy_cache", parameters=["off"]),
            Directive(name="add_header", parameters=["X-Cache", "$upstream_cache_status"]),
            add_loc
        ]

        idx = self.find_index(
            self.OpL("proxy_set_header", +1, "Remote-Host"),  # 放到ip黑白名单配置的后面
            self.OpL("proxy_set_header", +1, "Connection"),  # 放到ip黑白名单配置的后面
            self.OpL("gzip"),  # 放到gzip配置的前面
            self.OpL("sub_filter"),  # 放到sub_filter配置的前面
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
        )
        self.insert_after(max(0, idx), *add_list)


    def set_gzip(self, status: bool, level: int, min_size: str, gz_type: List[str]):
        # 先移除原有gzip相关指令
        block = self._location.get_block()
        gzip_names = [
            "gzip", "gzip_min_length", "gzip_buffers", "gzip_http_version", "gzip_comp_level",
            "gzip_types", "gzip_vary", "gzip_proxied", "gzip_disable"
        ]
        block.directives = [d for d in block.directives if d.get_name() not in gzip_names]
        if not status:
            return
        # 添加一组gzip配置
        add_dirs = [
            Directive(name="gzip", parameters=["on"], comment=["#GZIP 配置传输压缩"]),
            Directive(name="gzip_min_length", parameters=[min_size], inline_comment=["#GZIP 配置传输最小长度"]),
            Directive(name="gzip_buffers", parameters=["16 8k"], inline_comment=["#GZIP 配置传输缓存块"]),
            Directive(name="gzip_http_version", parameters=["1.1"], inline_comment=["#GZIP 配置传输协议版本"]),
            Directive(name="gzip_comp_level", parameters=[str(level)], inline_comment=["#GZIP 配置传输压缩级别"]),
            Directive(name="gzip_types", parameters=gz_type),
            Directive(name="gzip_vary", parameters=["on"]),
            Directive(name="gzip_proxied", parameters=["expired", "no-cache", "no-store", "private", "auth"]),
            Directive(name="gzip_disable", parameters=['"MSIE [1-6]\\."'], inline_comment=["#GZIP 拒绝过低版本浏览器压缩"]),
        ]

        idx = self.find_index(
            self.OpL("location", +1, ".*\.(css|js"),  # 放到ip黑白名单配置的后面
            self.OpL("proxy_ssl_server_name", +1),  # 放到ip黑白名单配置的后面
            self.OpL("proxy_set_header", +1, "Connection"),  # 放到ip黑白名单配置的后面
            self.OpR("deny", +1),  # 放到ip黑白名单配置的后面
            self.OpR("allow", +1),  # 放到ip黑白名单配置的后面
            self.OpL("sub_filter"),  # 放到sub_filter配置的前面
        )
        self.insert_after(min(len(self._block.directives), max(0, idx)), *add_dirs)

    def set_security_referer(
            self,
            status: bool = True,
            suffix_list: List[str] = None,
            domain_list: List[str] = None,
            return_rule: str = "404",
            allow_empty: bool = False):
        loc: Optional[Location] = None
        locs = self._location.top_find_directives_with_param("location", "~")
        if locs:
            for loc_if in locs:
                loc_obj = trans_(loc_if, Location)
                if not loc_obj:
                    continue
                if not loc_obj.match.startswith(r".*\.(") and not loc_obj.match.endswith(r")$"):
                    continue
                if loc_obj.top_find_directives("expires") and \
                        loc_obj.top_find_directives("valid_referers") and \
                        loc_obj.top_find_directives_like_param("if", "$invalid_referer"):
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

            self.insert_after(len(self._block.directives), loc)
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
                if_dir.block.directives = [
                    i for i in if_dir.block.directives
                    if i.get_name() not in ("return", "rewrite")]
                if_dir.block.directives.append(ret)

        return
