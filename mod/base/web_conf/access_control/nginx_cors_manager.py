import re
import sys

from .base import BaseCorsManager
from typing import List, Optional, Dict, Union


class NginxConfigManager(BaseCorsManager):
    """
set $bt_allowed_origin_flag "0";
set $bt_allowed_origin "";
if ($http_origin ~* "^https?://(192\.168\.69\.159|bt.cn)") {
  set $bt_allowed_origin_flag "1";
  set $bt_allowed_origin $http_origin;
}

add_header Access-Control-Allow-Origin "$bt_allowed_origin";
add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
add_header Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization";
add_header Access-Control-Expose-Headers "Content-Length,Content-Range";
add_header Access-Control-Allow-Credentials "true";

if ($request_method = 'OPTIONS') {
  set $bt_allowed_origin_flag "${bt_allowed_origin_flag}1";
}
if ($bt_allowed_origin_flag = '11'){
  return 204;
}
    """
    _can_use_lua = None

    @classmethod
    def can_use_lua_module(cls) -> bool:
        if cls._can_use_lua is not None:

            return cls._can_use_lua

        if "/www/server/panel/class" not in sys.path:
            sys.path.insert(0, "/www/server/panel/class")

        import public
        if cls._can_use_lua is None:
            # 查询lua_module 不为空
            cls._can_use_lua = public.ExecShell("/www/server/nginx/sbin/nginx -V 2>&1 | grep lua_nginx_module")[0].strip() != ''
        return cls._can_use_lua

    def _make_sub_conf(self,
                       allowed_origins: List[str],
                       allow_methods: Optional[str],
                       allow_headers: Optional[str],
                       expose_headers: Optional[str],
                       allow_credentials: bool) -> str:
        if not allowed_origins:
            return """# CORS配置
add_header Access-Control-Allow-Origin "*";
add_header Access-Control-Allow-Methods "{}";
add_header Access-Control-Allow-Headers "{}";
add_header Access-Control-Expose-Headers "{}";

if ($request_method = 'OPTIONS') {{
    return 204;
}}
""".format(allow_methods, allow_headers, expose_headers)

        origins = '|'.join(re.escape(origin) for origin in allowed_origins)
        return """# CORS配置
set $bt_allowed_origin_flag "0";
set $bt_allowed_origin "";
if ($http_origin ~* "^https?://({})") {{
  set $bt_allowed_origin_flag "1";
  set $bt_allowed_origin $http_origin;
}}

add_header Access-Control-Allow-Origin "$bt_allowed_origin";
add_header Access-Control-Allow-Methods "{}";
add_header Access-Control-Allow-Headers "{}";
add_header Access-Control-Expose-Headers "{}";
add_header Access-Control-Allow-Credentials "{}";

if ($request_method = 'OPTIONS') {{
  set $bt_allowed_origin_flag "${{bt_allowed_origin_flag}}1";
}}
if ($bt_allowed_origin_flag = '11'){{
  return 204;
}}
""".format(origins, allow_methods, allow_headers, expose_headers, str(allow_credentials).lower())

    def _add_to_main(self, main_conf: str) -> Optional[str]:
        # 判断多个虚拟机server配置的位置
        main_conf = self._remove_from_main(main_conf)
        block_index_list = []
        include_sub = "\n    include {};".format(self.access_control_file)
        for block in re.finditer(r'\s*server\s*{', main_conf):
            if block.start() == 0:
                block_index_list.append(block.end())
                continue
            last_annotation = main_conf.rfind('#', 0, block.start())
            newline_pos = main_conf.rfind('\n', 0, block.start())
            if last_annotation != -1 and newline_pos < last_annotation < block.start():
                continue
            else:
                block_index_list.append(block.end())

        for idx in block_index_list[::-1]:
            main_conf = main_conf[:idx] + include_sub + main_conf[idx:]
        return main_conf

#     def add_cors(self,
#                  allowed_origins: List[str] = None,
#                  allow_credentials: bool = False,
#                  allow_methods: Optional[str] = None,
#                  allow_headers: Optional[str] = None,
#                  expose_headers: Optional[str] = None) -> Optional[str]:
#         """
#         添加CORS配置
#         :param allowed_origins: 允许的源列表，如果为None则允许所有源
#         :param allow_credentials: 是否允许凭据，默认为False
#         :param allow_methods: 允许的HTTP方法，默认为"GET, POST, OPTIONS, PUT, DELETE"
#         :param allow_headers: 允许的HTTP头，默认为"DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
#         :param expose_headers: 暴露的HTTP头，默认为"Content-Length,Content-Range"
#         """
#         # 默认值
#         allow_methods = allow_methods or "GET, POST, OPTIONS, PUT, DELETE"
#         allow_headers = allow_headers or "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
#         expose_headers = expose_headers or "Content-Length,Content-Range"
#         allow_credentials = str(allow_credentials).lower()
#         if isinstance(allowed_origins, (list, tuple)) and '*' in allowed_origins:
#             allowed_origins = [origin for origin in allowed_origins if origin != '*']
#
#         # 默认的CORS配置
#         cors_config = """
#     # CORS configuration
#     add_header 'Access-Control-Allow-Origin' '*';
#     add_header 'Access-Control-Allow-Methods' '{allow_methods}';
#     add_header 'Access-Control-Allow-Headers' '{allow_headers}';
#     add_header 'Access-Control-Expose-Headers' '{expose_headers}';
# """.format(allow_methods=allow_methods, allow_headers=allow_headers, expose_headers=expose_headers)
#
#         # 如果指定了允许的源
#         if allowed_origins:
#             origins = '|'.join(re.escape(origin) for origin in allowed_origins)  # 修改这里，对每个origin进行转义
#             cors_config = """
#     # CORS configuration
#     if ($http_origin ~* ^https?://({origins})$) {{
#         add_header 'Access-Control-Allow-Origin' $http_origin;
#         add_header 'Access-Control-Allow-Methods' '{allow_methods}';
#         add_header 'Access-Control-Allow-Headers' '{allow_headers}';
#         add_header 'Access-Control-Expose-Headers' '{expose_headers}';
#         add_header 'Access-Control-Allow-Credentials' '{allow_credentials}';
#     }}
#
#     if ($request_method = 'OPTIONS') {{
#         add_header 'Access-Control-Max-Age' 1728000;
#         add_header 'Content-Type' 'text/plain charset=UTF-8';
#         add_header 'Content-Length' 0;
#         return 204;
#     }}
# """.format(origins=origins, allow_methods=allow_methods, allow_headers=allow_headers, expose_headers=expose_headers, allow_credentials=allow_credentials)
#
#         # 在server块中添加CORS配置
#         return self._replace_config_data(cors_config)

    def _remove_from_main(self, main_conf: str) -> str:
        regexp = re.compile(r'\s*include\s+{}\s*;'.format(re.escape(self.access_control_file)))
        return regexp.sub('', main_conf)

    def _get_main_status(self) -> bool:
        regexp = re.compile(r'\s*include\s+{}\s*;'.format(re.escape(self.access_control_file)))
        return bool(regexp.search(self.read_main_config()))

    def _get_sub_data(self) -> Optional[Dict[str, Union[str, bool, list]]]:
        sub_conf = self.read_sub_config()
        if not sub_conf:
            return None
        regexp_dict: Dict[str, re.Pattern] = {
            'allowed_origins': re.compile(r"add_header\s+['\"]*Access-Control-Allow-Origin['\"]*\s+['\"]([^'\"]+)['\"]"),
            'allow_methods': re.compile(r"add_header\s+['\"]*Access-Control-Allow-Methods['\"]*\s+['\"]([^'\"]+)['\"]"),
            'allow_headers': re.compile(r"add_header\s+['\"]*Access-Control-Allow-Headers['\"]*\s+['\"]([^'\"]+)['\"]"),
            'expose_headers': re.compile(r"add_header\s+['\"]*Access-Control-Expose-Headers['\"]*\s+['\"]([^'\"]+)['\"]"),
            'allow_credentials': re.compile(r"add_header\s+['\"]*Access-Control-Allow-Credentials['\"]*\s+['\"]([^'\"]+)['\"]"),
        }
        res_data: Dict[str, Union[str, bool, list]]= {}
        for key, regexp in regexp_dict.items():
            match = regexp.search(sub_conf)
            if match:
                res_data[key] = match.group(1)
            else:
                res_data[key] = ""
            if key == 'allow_credentials':
                res_data["allow_credentials"] = (res_data["allow_credentials"] == 'true')
            if key == 'allowed_origins':
                if res_data[key] == "*":
                    res_data[key] = []
                else:
                    regexp = re.compile(r"\^https\?://\((.*)\)")
                    res = regexp.search(sub_conf)
                    if not res:
                        res_data[key] = []
                    else:
                        unescape = lambda s: s.replace('\.', '.').replace('\*', '.*')  # 简单处理域名可能遇到的情况
                        res_data[key]  = [unescape(origin.strip()) for origin in res.group(1).split('|')]

        return res_data


class NginxLuaConfigManager(NginxConfigManager):
    """# 使用lua完成跨域，因为部分阶段已使用。故采取 set_by_lua_block"""

    _LUA_FORMAT = """
# 使用lua完成跨域，因为部分阶段已使用。故采取 set_by_lua_block
set $cors_config '0';
set_by_lua_block $cors_config {{
    local origin = ngx.req.get_headers()["Origin"]
    local is_allowed = false
    local allowed_origins = {{{allowed_origins}}}
    local allow_methods = "{allow_methods}"
    local allow_headers = "{allow_headers}"
    local expose_headers = "{expose_headers}"
    local allow_credentials = {allow_credentials}

    if origin then
        -- 处理空白名单逻辑
        if #allowed_origins == 0 then
            is_allowed = true
            origin = "*"
        else
            for _, allowed in ipairs(allowed_origins) do
                if origin == allowed then
                    is_allowed = true
                    break
                end
            end
        end

        if is_allowed then
            ngx.header["Access-Control-Allow-Origin"] = origin
            ngx.header["Access-Control-Allow-Methods"] = allow_methods
            ngx.header["Access-Control-Allow-Headers"] = allow_headers
            ngx.header["Access-Control-Expose-Headers"] = expose_headers

            -- 安全设置：当origin不是*时，才允许credentials
            if origin ~= "*" and allow_credentials then
                ngx.header["Access-Control-Allow-Credentials"] = "true"
            end
        end
    end

    -- 处理OPTIONS请求
    if ngx.var.request_method == "OPTIONS" and is_allowed then
        ngx.header["Access-Control-Max-Age"] = 1728000
        ngx.header["Content-Type"] = "text/plain charset=UTF-8"
        ngx.header["Content-Length"] = "0"
        return "1"
    end
    return "0"
}}

if ($cors_config = "1") {{
    return 204;
}}"""

    # 新增方法：获取当前CORS配置
    def _make_sub_conf(self,
                       allowed_origins: List[str],
                       allow_methods: Optional[str],
                       allow_headers: Optional[str],
                       expose_headers: Optional[str],
                       allow_credentials: bool) -> str:

        if not allowed_origins:
            allowed_origins = ""
        else:
            allowed_origins = ",".join(
                ('"https://{domain}","http://{domain}"'.format(domain=domain) for domain in allowed_origins)
            )

        return self._LUA_FORMAT.format(
            allowed_origins=allowed_origins,
            allow_methods=allow_methods,
            allow_headers=allow_headers,
            expose_headers=expose_headers,
            allow_credentials=str(allow_credentials).lower()
        )

    def _get_sub_data(self) -> Optional[Dict[str, Union[str, bool, list]]]:
        sub_conf = self.read_sub_config()
        if not sub_conf:
            return None
        regexp_dict: Dict[str, re.Pattern] = {
            'allowed_origins': re.compile(r"local\s+allowed_origins\s*=\s*\{(?P<target>[^}]*)}"),
            'allow_methods': re.compile(r'local\s+allow_methods\s*=\s*"(?P<target>.*)"'),
            'allow_headers': re.compile(r'local\s+allow_headers\s*=\s*"(?P<target>.*)"'),
            'expose_headers': re.compile(r'local\s+expose_headers\s*=\s*"(?P<target>.*)"'),
            'allow_credentials': re.compile(r'local\s+allow_credentials\s*=\s*(?P<target>.*)'),
        }

        res_data: Dict[str, Union[str, bool, list]] = {}
        for key, regexp in regexp_dict.items():
            match = regexp.search(sub_conf)
            if match:
                res_data[key] = match.group('target')
            else:
                res_data[key] = ""

            if key == 'allow_credentials':
                res_data["allow_credentials"] = (res_data["allow_credentials"] == 'true')

            if key == 'allowed_origins':
                if res_data[key] == "":
                    res_data[key] = []
                else:
                    tmp_list = [origin.strip('"') for origin in res_data[key].split(',')]
                    res_data[key] = [origin[8:] for origin in tmp_list if origin.startswith('https://')]

        return res_data

