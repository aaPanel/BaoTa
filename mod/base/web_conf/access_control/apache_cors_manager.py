import re
from .base import BaseCorsManager
from typing import List, Optional, Dict, Union


class ApacheConfigManager(BaseCorsManager):
    """
# CORS configuration
SetEnvIf Origin "^https?://(192\.168\.69\.159|192\.168\.69\.154)$" AccessControlAllowOrigin=$0
Header always set Access-Control-Allow-Origin %{AccessControlAllowOrigin}e env=AccessControlAllowOrigin
Header always set Access-Control-Allow-Methods "GET,POST,OPTIONS,PUT,DELETE"
Header always set Access-Control-Allow-Headers "DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization"
Header always set Access-Control-Expose-Headers "Content-Length,Content-Range"
Header always set Access-Control-Allow-Credentials "false"

<IfModule mod_rewrite.c>
    RewriteEngine On
    # 检查是否设置了 AccessControlAllowOrigin 环境变量
    RewriteCond %{ENV:AccessControlAllowOrigin} ^https?://(192\.168\.69\.159|192\.168\.69\.154)$
    RewriteCond %{REQUEST_METHOD} OPTIONS
    Header always set Access-Control-Max-Age 1728000
    RewriteRule ^(.*)$ $1 [R=204,L]
</IfModule>
    """

    def _make_sub_conf(self,
                       allowed_origins: List[str],
                       allow_methods: Optional[str],
                       allow_headers: Optional[str],
                       expose_headers: Optional[str],
                       allow_credentials: bool) -> str:

        if not allowed_origins:
            return """# CORS configuration
Header always set Access-Control-Allow-Origin "*"
Header always set Access-Control-Allow-Methods "{}"
Header always set Access-Control-Allow-Headers "{}"
Header always set Access-Control-Expose-Headers "{}"

<IfModule mod_rewrite.c>
    RewriteEngine On
    RewriteCond %{{REQUEST_METHOD}} OPTIONS
    Header always set Access-Control-Max-Age 1728000
    RewriteRule ^(.*)$ - [R=204,L]
</IfModule>
""".format(allow_methods, allow_headers, expose_headers)

        origin = '|'.join(re.escape(origin) for origin in allowed_origins)
        return """# CORS configuration
SetEnvIf Origin "^https?://({origin})$" AccessControlAllowOrigin=$0
Header always set Access-Control-Allow-Origin %{{AccessControlAllowOrigin}}e env=AccessControlAllowOrigin
Header always set Access-Control-Allow-Methods "{allow_methods}"
Header always set Access-Control-Allow-Headers "{allow_headers}"
Header always set Access-Control-Expose-Headers "{expose_headers}"
Header always set Access-Control-Allow-Credentials "{allow_credentials}"

<IfModule mod_rewrite.c>
    RewriteEngine On
    # 检查是否设置了 AccessControlAllowOrigin 环境变量
    RewriteCond %{{ENV:AccessControlAllowOrigin}} ^https?://({origin})$
    RewriteCond %{{REQUEST_METHOD}} OPTIONS
    Header always set Access-Control-Max-Age 1728000
    RewriteRule ^(.*)$ - [R=204,L]
</IfModule>
""".format(origin=origin,
           allow_methods=allow_methods,
           allow_headers=allow_headers,
           expose_headers=expose_headers,
           allow_credentials=str(allow_credentials).lower())

    def _add_to_main(self, main_conf: str) -> str:
        # 判断多个虚拟机server配置的位置
        main_conf = self._remove_from_main(main_conf)
        block_index_list = []
        include_sub = "\n    IncludeOptional {}".format(self.access_control_file)
        for block in re.finditer(r'\s*<VirtualHost\s+[^>]+>', main_conf):
            start_pos = block.start()
            if start_pos == 0:
                block_index_list.append(block.end())
                continue
            last_annotation = main_conf.rfind('#', 0, start_pos)
            newline_pos = main_conf.rfind('\n', 0, start_pos)
            if last_annotation != -1 and newline_pos < last_annotation < start_pos:
                continue
            else:
                block_index_list.append(block.end())

        for idx in block_index_list[::-1]:
            main_conf = main_conf[:idx] + include_sub + main_conf[idx:]
        return main_conf

    def _remove_from_main(self, main_conf: str) -> str:
        # 删除虚拟机server配置
        return re.sub(r'\s*IncludeOptional\s+{}'.format(re.escape(self.access_control_file)), '', main_conf)

    def _get_main_status(self) -> bool:
        # 获取虚拟机server配置状态
        main_conf = self.read_main_config()
        return bool(re.search(r'\s*IncludeOptional\s+{}'.format(re.escape(self.access_control_file)), main_conf))

    def _get_sub_data(self) -> Optional[Dict[str, Union[str, bool, list]]]:
        sub_conf = self.read_sub_config()
        if not sub_conf:
            return None

        # 匹配正则表达式
        regexp_dict: Dict[str, re.Pattern] = {
            "allowed_origins": re.compile(r"\^https\?://\((?P<target>.*)\)\$"),
            "allow_methods": re.compile(
                r'Header\s+always\s+set\s+[\'"]*Access-Control-Allow-Methods[\'"]*\s+[\'"]*(?P<target>.*)[\'"]*'
            ),
            "allow_headers": re.compile(
                r'Header\s+always\s+set\s+[\'"]*Access-Control-Allow-Headers[\'"]*\s+[\'"]*(?P<target>.*)[\'"]*'
            ),
            "expose_headers": re.compile(
                r'Header\s+always\s+set\s+[\'"]*Access-Control-Expose-Headers[\'"]*\s+[\'"]*(?P<target>.*)[\'"]*'
            ),
            "allow_credentials": re.compile(
                r'Header\s+always\s+set\s+[\'"]*Access-Control-Allow-Credentials[\'"]*\s+[\'"]*(?P<target>.*)[\'"]*'
            )
        }

        res_data: Dict[str, Union[str, bool, list]]= {}
        for key, regexp in regexp_dict.items():
            match = regexp.search(sub_conf)
            if match:
                res_data[key] = match.group("target").strip('"\'')
            else:
                res_data[key] = ""
            if key == 'allow_credentials':
                res_data["allow_credentials"] = (res_data["allow_credentials"] == 'true')

            if key == 'allowed_origins':
                tmp = res_data[key].split("|")
                unescape = lambda s: s.replace('\.', '.').replace('\*', '.*')  # 简单处理域名可能遇到的情况
                res_data[key]  = [unescape(origin.strip()) for origin in tmp]

        return res_data
