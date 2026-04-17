import os
import re
import subprocess
import json
from typing import Optional, Tuple, List


class NgInfo:
    __slots__ = ("_ng_bin", "_ng_conf", "_V_OUT", "_modules", "_listen_ipv6", "_tls_list")

    def __init__(self, ng_bin: str, ng_conf: str=""):
        self._ng_bin = ng_bin
        self._ng_conf = ng_conf
        self._V_OUT: Optional[str] = None
        self._modules: Optional[List[str]]= None
        self._listen_ipv6 = None
        self._tls_list = None
        if ng_bin == "/www/server/nginx/sbin/nginx" and (not os.path.exists(ng_bin) or not os.path.exists(ng_conf)):
            return
        if not os.path.isfile(ng_bin):
            raise ValueError("Nginx binary path does not exist")
        if not os.access(ng_bin, os.X_OK):
            raise ValueError("Nginx binary is not executable")
        if ng_conf:
            if not os.path.isfile(ng_conf):
                raise ValueError("Nginx conf path does not exist")
            if not os.access(ng_conf, os.R_OK):
                raise ValueError("Nginx conf is not readable")

    @property
    def _v_out(self) -> str:
        if self._V_OUT is None:
            # 使用 io + subprocess 获取所有输出（stderr + stdout）
            try:
                self._V_OUT = subprocess.check_output([self._ng_bin, "-V"], stderr=subprocess.STDOUT).decode()
            except:
                self._V_OUT = ""
        return self._V_OUT

    @property
    def version(self) -> Optional[Tuple[int, int, int]]:
        """获取 Nginx 版本"""
        ver_regexp = re.compile(r"nginx\s+version.*/(?P<ver>\d+\.\d+(\.\d+)*)")
        res = ver_regexp.search(self._v_out)
        if not res:
            return None
        ver = res.group("ver")
        ver_list = [int(i) for i in ver.split(".")]
        if len(ver_list) < 3:
            ver_list.extend([0] * (3 - len(ver_list)))
        if len(ver_list) > 3:
            ver_list = ver_list[:3]
        return ver_list[0], ver_list[1], ver_list[2]

    @property
    def openssl_version(self) -> Optional[Tuple[int, int, int]]:
        openssl_regexp = re.compile(r"built\s+with\s+OpenSSL\s+(?P<ver>[\d.]+)")
        search = openssl_regexp.search(self._v_out)
        if not search:
            return None
        ver: List[str] = search.group("ver").split(".")
        if len(ver) < 3:
            ver.extend(['0'] * (3 - len(ver)))
        ver_list = []
        for i in range(3):
            try:
                ver_list.append(int(ver[i]))
            except:
                ver_list.append(0)
        return ver_list[0], ver_list[1], ver_list[2]

    @property
    def modules(self) -> List[str]:
        """获取 Nginx 模块列表

        nginx version: nginx/1.28.0
        built by gcc 12.2.0 (Debian 12.2.0-14+deb12u1)
        built with OpenSSL 3.5.4 30 Sep 2025
        TLS SNI support enabled
        configure arguments: --user=www --group=www --prefix=/www/server/nginx --add-module=/www/server/nginx/src/ngx_devel_kit --add-module=/www/server/nginx/src/lua_nginx_module --add-module=/www/server/nginx/src/ngx_cache_purge --add-module=/www/server/nginx/src/nginx-sticky-module-ng-1.3.0 --with-openssl=/www/server/nginx/src/openssl --with-pcre=pcre-8.43 --with-http_v2_module --with-stream --with-stream_ssl_module --with-stream_ssl_preread_module --with-http_stub_status_module --with-http_ssl_module --with-http_image_filter_module --with-http_gzip_static_module --with-http_gunzip_module --with-ipv6 --with-http_sub_module --with-http_flv_module --with-http_addition_module --with-http_realip_module --with-http_mp4_module --with-http_auth_request_module --add-module=/www/server/nginx/src/ngx_http_substitutions_filter_module-master --with-ld-opt=-Wl,-E --with-cc-opt=-Wno-error --with-ld-opt=-ljemalloc --with-http_dav_module --add-module=/www/server/nginx/src/nginx-dav-ext-module --with-http_v3_module

        """
        if self._modules is not None:
            return self._modules

        with_module_regexp = re.compile(r"--with-(?P<module>\w+_module)\s+")
        add_module_regexp = re.compile(r"--add-module=/([^\s/]+/)+(?P<module>[a-zA-Z-_]+)")
        modules_list = []
        for tmp_module in with_module_regexp.finditer(self._v_out):
            modules_list.append(tmp_module.group("module"))

        for tmp_module in add_module_regexp.finditer(self._v_out):
            add_str = tmp_module.group("module")
            if "module" in add_str:
                add_str = add_str[:add_str.index("module")]
            add_str.replace("-", "_")
            if add_str not in modules_list:
                modules_list.append(add_str)
            add_module_str = "{}_module".format(add_str)
            if add_module_str not in modules_list:
                modules_list.append(add_module_str)

        self._modules = modules_list

        return self._modules

    def has_module(self, module_name: str) -> bool:
        """判断 Nginx 是否有指定模块"""
        module_name = module_name.replace("-", "_")
        return module_name in self.modules

    def http3_enabled(self):
        return self.has_module("http_v3_module") and self.ssl_early_data_enabled()

    def http2_enabled(self):
        return self.has_module("http_v2_module")

    def listen_http2_enabled(self):
        return self.http2_enabled() and  (1, 9, 5) <= self.version < (1, 25, 1)

    def http2_on_enabled(self):
        return self.http2_enabled() and self.version >= (1, 25, 1)

    def ssl_early_data_enabled(self):
        if not self.openssl_version:
            return False
        return self.openssl_version >= (3, 5, 1)

    def listen_ipv6(self) -> bool:
        """判断 Nginx 是否支持 IPv6"""
        if self._listen_ipv6 is not None:
            return self._listen_ipv6
        if "--with-ipv6" not in self._v_out:
            return False
        self._listen_ipv6 = os.path.exists('/www/server/panel/data/ipv6.pl')
        return self._listen_ipv6

    def tls_versions(self) -> List[str]:
        """获取支持的 TLS 版本"""
        if self._tls_list is not None:
            return self._tls_list

        protocols = {
            "TLSv1": False,
            "TLSv1.1": True,
            "TLSv1.2": True,
            "TLSv1.3": True,
        }
        try:
            file_path = "/www/server/panel/data/ssl_protocol.json"
            with open(file_path, "r") as f:
                tmp_protocols = json.load(f)
            for k, v in tmp_protocols.items():
                if k in protocols and isinstance(v, bool):
                    protocols[k] = v
        except:
            pass
        self._tls_list = [v for v, s in protocols.items() if s]
        return self._tls_list

    @staticmethod
    def default_http2https():
        http2https_pl = "/www/server/panel/data/http2https.pl"
        return os.path.exists(http2https_pl)



DEFAULT_NGINX = __default_nginx = NgInfo(
    "/www/server/nginx/sbin/nginx",
    "/www/server/nginx/conf/nginx.conf",
)


def use_nginx(nginx_bin: str = "", nginx_conf: str = "") -> None:
    """使用指定的 Nginx 二进制文件"""
    global DEFAULT_NGINX
    DEFAULT_NGINX = NgInfo(nginx_bin, nginx_conf)


def reset_nginx() -> None:
    """重置为默认的 Nginx"""
    global DEFAULT_NGINX, __default_nginx
    DEFAULT_NGINX = __default_nginx
