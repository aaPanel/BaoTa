import os
import re
from typing import List, Callable, Dict, Optional, Tuple, Union
from dataclasses import dataclass, field
from .. import IDirective, Directive

_VAR_PATTERN = re.compile(r'\$\w+|\$\{[^}]+}')  # 匹配 $var 或 ${var}
_UNIX_PREFIX = 'unix:'


def _process_lua_package_path(directive: IDirective, base_path: str) -> List[str]:
    """
    智能处理 lua_package_path / lua_package_cpath
    保留变量/通配符，仅转换无变量的相对路径片段
    """
    if not directive.parameters or not directive.parameters[0]:
        return directive.parameters

    path_str = directive.parameters[0].strip('"').strip("'")
    # 保留空片段（双分号表示当前目录）
    fragments = path_str.split(';')
    processed = []

    for frag in fragments:
        if not frag:  # 保留空片段（;; 中的空）
            processed.append('')
            continue
        frag = _resolve_mixed_path(frag, base_path)
        processed.append(frag)

    directive.parameters[0] = '"{}"'.format(';'.join(processed))
    return directive.parameters


def _is_safe_path_fragment(frag: str) -> bool:
    """检查路径片段是否安全 (不含目录遍历)"""
    return ".." not in frag and "~" not in frag and not frag.startswith("/")


def _resolve_mixed_path(path_str: str, base_path: str) -> str:
    """智能转换含变量的混合路径，保留变量部分"""
    if not path_str or path_str.startswith('/') or '://' in path_str:
        return path_str

    # 查找第一个变量位置
    match = _VAR_PATTERN.search(path_str)
    if match:
        static_part = path_str[:match.start()].rstrip("/\\")
        dynamic_part = path_str[match.start():]
    else:
        static_part, dynamic_part = path_str.rstrip("/\\"), ""

    # 仅当静态部分非空且不含危险字符时转换
    if static_part and _is_safe_path_fragment(static_part):
        try:
            abs_static = os.path.normpath(os.path.join(base_path, static_part))
            abs_static = abs_static.replace('\\', '/')  # 统一为 POSIX 风格
            # 保留原始路径中的斜杠风格 (变量前添加斜杠)
            separator = "/" if path_str[len(static_part):0] in ("/", "\\") else ""
            return f"{abs_static}{separator}{dynamic_part}"
        except Exception:
            pass

    return path_str  # 转换失败或不安全时保留原值


def _process_fancyindex_header_footer(directive: Directive, base_path: str) -> List[str]:
    """智能处理 fancyindex_header/footer，仅当使用 local 模式时转换路径"""
    if len(directive.parameters) < 1:
        return directive.parameters

    # 检查是否为 local 模式
    is_local_mode = (
        len(directive.parameters) >= 2
        and directive.parameters[1] == "local"
    )

    if is_local_mode:
        directive.parameters[0] = _resolve_mixed_path(directive.parameters[0], base_path)
    # subrequest 模式 (默认) 保持原样

    return directive.parameters

def _process_simple_path(directive: Directive, base_path: str) -> List[str]:
    """处理单路径参数指令（含变量支持）"""
    if directive.parameters:
        directive.parameters[0] = _resolve_mixed_path(directive.parameters[0], base_path)
    return directive.parameters


def _process_unix_socket(directive: Directive, base_path: str) -> List[str]:
    """处理 unix:/path 形式的参数"""
    if not directive.parameters:
        return directive.parameters

    val = directive.parameters[0]
    if not val.startswith(_UNIX_PREFIX):
        return directive.parameters

    path_part = val[len(_UNIX_PREFIX):].lstrip()
    if not path_part:
        return directive.parameters

    # 保留查询参数/片段 (罕见但合法)
    path_core, sep, extras = path_part.partition("?")
    path_core, sep2, extras2 = path_core.partition("#")
    extras = sep + extras + sep2 + extras2

    # 仅转换核心路径部分
    new_core = _resolve_mixed_path(path_core, base_path)
    directive.parameters[0] = f"{_UNIX_PREFIX}{new_core}{extras}"
    return directive.parameters


def _process_upstream_server(directive: Directive, base_path: str) -> List[str]:
    """仅当 server 在 upstream 块内时处理 unix socket"""
    return _process_unix_socket(directive, base_path)



# =============== 指令映射表（严格筛选：仅文件系统路径指令） ===============
# 不包含 include 指令， include 在写入和解析的时候处理
PATH_DIRECTIVES: Dict[str, Tuple[str, Callable[[Directive, str], List[str]]]] = {
    # --- 基准: --prefix (绝大多数指令) ---
    'root': ('prefix', _process_simple_path),  # http_core (高频)
    'alias': ('prefix', _process_simple_path),  # http_core (高频)
    'client_body_temp_path': ('prefix', _process_simple_path),  # http_core (高频)
    'error_log': ('prefix', _process_simple_path),  # core (高频)
    'pid': ('prefix', _process_simple_path),  # core (高频)
    'lock_file': ('prefix', _process_simple_path),  # core (中频)
    'load_module': ('prefix', _process_simple_path),  # core (中频)
    'access_log': ('prefix', _process_simple_path),  # http_log, stream_log (高频)

    # --- SSL/TLS 证书/密钥 (高频) ---
    'ssl_certificate': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl
    'ssl_certificate_key': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl
    'ssl_client_certificate': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl
    'ssl_trusted_certificate': ('config_dir', _process_simple_path),
    # http_ssl, mail_ssl, stream_ssl, http_acme, http_oidc, ngx_mgmt_module
    'ssl_crl': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl, http_oidc, ngx_mgmt_module
    'ssl_dhparam': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl
    'ssl_stapling_file': ('config_dir', _process_simple_path),  # http_ssl, stream_ssl
    'ssl_session_ticket_key': ('config_dir', _process_simple_path),  # http_ssl, mail_ssl, stream_ssl
    'ssl_password_file': ('config_dir', _process_simple_path),  # http_ssl, stream_ssl
    'ssl_key_log': ('prefix', _process_simple_path),  # http_ssl, stream_ssl
    'ssl_ech_file': ('prefix', _process_simple_path),  # http_ssl, stream_ssl

    # --- 代理缓存存储路径 (中频) ---
    'proxy_temp_path': ('prefix', _process_simple_path),  # http_proxy
    'proxy_store': ('prefix', _process_simple_path),  # http_proxy
    'proxy_cache_path': ('prefix', _process_simple_path),  # http_proxy
    'proxy_ssl_certificate': ('config_dir', _process_simple_path),  # http_proxy, stream_proxy
    'proxy_ssl_certificate_key': ('config_dir', _process_simple_path),  # http_proxy, stream_proxy
    'proxy_ssl_crl': ('config_dir', _process_simple_path),  # http_proxy, stream_proxy
    'proxy_ssl_password_file': ('config_dir', _process_simple_path),  # http_proxy, stream_proxy
    'proxy_ssl_trusted_certificate': ('config_dir', _process_simple_path),  # http_proxy, stream_proxy

    'fastcgi_temp_path': ('prefix', _process_simple_path),  # http_fastcgi
    'fastcgi_store': ('prefix', _process_simple_path),  # http_fastcgi
    'fastcgi_cache_path': ('prefix', _process_simple_path),  # http_fastcgi

    'uwsgi_temp_path': ('prefix', _process_simple_path),  # http_uwsgi
    'uwsgi_store': ('prefix', _process_simple_path),  # http_uwsgi
    'uwsgi_cache_path': ('prefix', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_certificate': ('config_dir', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_certificate_key': ('config_dir', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_crl': ('config_dir', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_key_log': ('prefix', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_password_file': ('config_dir', _process_simple_path),  # http_uwsgi
    'uwsgi_ssl_trusted_certificate': ('config_dir', _process_simple_path),  # http_uwsgi

    'scgi_temp_path': ('prefix', _process_simple_path),  # http_scgi
    'scgi_store': ('prefix', _process_simple_path),  # http_scgi
    'scgi_cache_path': ('prefix', _process_simple_path),  # http_scgi

    # --- 认证/授权 (中频) ---
    'auth_basic_user_file': ('prefix', _process_simple_path),  # http_auth_basic
    'auth_jwt_key_file': ('prefix', _process_simple_path),  # http_auth_jwt

    # --- GeoIP 数据库 (低频) ---
    'geoip_country': ('prefix', _process_simple_path),  # http_geoip, stream_geoip (官方已弃用)
    'geoip_city': ('prefix', _process_simple_path),  # http_geoip, stream_geoip (官方已弃用)
    'geoip_org': ('prefix', _process_simple_path),  # http_geoip, stream_geoip (官方已弃用)

    # --- 模块专用路径 (低频) ---
    'xslt_stylesheet': ('prefix', _process_simple_path),  # http_xslt
    'perl_modules': ('prefix', _process_simple_path),  # http_perl
    'perl_require': ('prefix', _process_simple_path),  # http_perl
    'google_perftools_profiles': ('prefix', _process_simple_path),  # google_perftools
    'state_path': ('prefix', _process_simple_path),  # http_acme, ngx_mgmt_module
    'hls_fragment': ('prefix', _process_simple_path),  # http_hls

    # --- NJS 模块 (新兴) ---
    'js_import': ('prefix', _process_simple_path),  # njs
    'js_path': ('prefix', _process_simple_path),  # njs
    'js_include': ('prefix', _process_simple_path),  # njs
    'js_fetch_trusted_certificate': ('prefix', _process_simple_path),  # njs

    # --- Unix Socket 专用 (中频) ---
    'fastcgi_pass': ('prefix', _process_unix_socket),  # http_fastcgi (unix:/path)
    'proxy_pass': ('prefix', _process_unix_socket),  # http_proxy, stream_proxy (unix:/path)
    'uwsgi_pass': ('prefix', _process_unix_socket),  # http_uwsgi (unix:/path)
    'scgi_pass': ('prefix', _process_unix_socket),  # http_scgi (unix:/path)
    'grpc_pass': ('prefix', _process_unix_socket),  # http_grpc (unix:/path)
    'memcached_pass': ('prefix', _process_unix_socket),  # http_memcached (unix:/path)
    'tunnel_pass': ('prefix', _process_unix_socket),  # http_tunnel (unix:/path)
    'auth_http': ('prefix', _process_unix_socket),  # mail_auth_http (unix:/path)

    # --- 上下文敏感 (upstream server) ---
    'server': ('prefix', _process_upstream_server),  # http_upstream, stream_upstream

    # --- 第三方模块（按需取消注释）---
    'geoip2': ('prefix', _process_simple_path),           # ngx_http_geoip2_module

    'fancyindex_header': ('prefix', _process_fancyindex_header_footer),
    'fancyindex_footer': ('prefix', _process_fancyindex_header_footer),
    'vhost_traffic_status_dump': ('prefix', _process_simple_path),
    'lua_package_path': ('prefix', _process_lua_package_path),
    'lua_package_cpath': ('prefix', _process_lua_package_path),
    'lua_ssl_trusted_certificate': ('prefix', _process_simple_path),
}
PATH_DIRECTIVES_REGEXP: List[Tuple[re.Pattern, Tuple[str, Callable[[Directive, str], List[str]]]]] = [
    (re.compile(r'^upload(_state)?_store$'), ('prefix', _process_simple_path)),    # ngx_upload_module
    (re.compile(r'^\w+_lua_file$'), ('prefix', _process_simple_path)),  # 及其他 *_by_lua_file
]


# =============== 主转换函数 ===============
def normalize_directive_paths(
        directive: Directive,
        prefix_path: str,
        config_dir: str,
        strict: bool = False,
        **block_env
) -> bool:
    """
    原地转换 Directive.parameters 中的相对路径（支持含变量路径）

    :param directive: 待处理的 Directive 对象（直接修改 parameters）
    :param prefix_path: Nginx --prefix 路径（建议绝对路径）
    :param config_dir: Nginx 配置文件所在目录
    :param strict: True 时遇错抛异常；False 时静默跳过
    :param block_env: 当前指令块 (upstream=False) 解决冲突的情况
    :return: 是否命中需处理的指令
    """
    if not directive.get_name() or not directive.parameters:
        return False
    if directive.get_name() == "server" and not 'upstream' in block_env:
        return False

    rule = PATH_DIRECTIVES.get(directive.get_name())
    if not rule:
        for regexp, tmp_rule in PATH_DIRECTIVES_REGEXP:
            if regexp.match(directive.get_name()):
                rule = tmp_rule
                break
    if not rule:
        return False

    rel_type, processor = rule

    try:
        if rel_type == 'prefix':
            processor(directive, prefix_path)  # 原地修改 directive.parameters
        else:
            processor(directive, config_dir)
        return True
    except Exception as e:
        if strict:
            raise RuntimeError(
                f"Path normalization failed for '{directive.get_name()}' at line {directive.line}: {e}"
            ) from e
        return False