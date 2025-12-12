import json
import os.path
import shutil
import sys

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

from .ip_restrict import IpRestrict, RealIpRestrict
from .redirect import RealRedirect, Redirect
from .access_restriction import AccessRestriction, RealAccessRestriction
from .domain_tool import domain_to_puny_code, check_domain, normalize_domain, NginxDomainTool, ApacheDomainTool, \
    is_domain
from .dns_api import DNSApiManager, RealDnsMager
from .dir_tool import DirTool
from .referer import Referer, RealReferer
from .logmanager import LogMgr, RealLogMgr
from .proxy import Proxy, RealProxy
from .ssl import SSLManager, RealSSLManger
from .config_mgr import ConfigMgr
from .default_site import set_default_site, get_default_site, check_default
from .access_control import cors_manager
from .nginx_gzip import NginxGzipMgr
from .nginx_cache import NginxStaticCacheMgr
from .server_extension import NginxExtension as ng_ext, ApacheExtension as ap_ext


def remove_sites_service_config(site_name: str, config_prefix: str = ""):
    """
    用于删除一个网站的nginx，apache的所有相关配置文件和配置项
    包含：
        配置文件，访问限制, 反向代理, 重定向, 防盗链，证书目录, IP黑白名单, 历史配置文件, 默认站点, 日志格式配置记录, 伪静态等
    """
    # 配置文件
    ng_file = "/www/server/panel/vhost/nginx/{}{}.conf".format(config_prefix, site_name)
    if os.path.exists(ng_file):
        os.remove(ng_file)
    ap_file = "/www/server/panel/vhost/apache/{}{}.conf".format(config_prefix, site_name)
    if os.path.exists(ap_file):
        os.remove(ap_file)

    ng_ext.remove_extension(site_name, ng_file)
    ap_ext.remove_extension(site_name, ap_file)
    # 访问限制
    RealAccessRestriction(config_prefix=config_prefix).remove_site_access_restriction_info(site_name)
    # 反向代理
    RealProxy(config_prefix=config_prefix).remove_site_proxy_info(site_name)
    # 重定向
    RealRedirect(config_prefix=config_prefix).remove_site_redirect_info(site_name)
    # 防盗链
    RealReferer(config_prefix=config_prefix).remove_site_referer_info(site_name)
    # 证书目录
    cert_path = "/www/server/panel/vhost/cert/" + site_name
    if os.path.isdir(cert_path):
        shutil.rmtree(cert_path)
    # IP黑白名单
    RealIpRestrict(config_prefix=config_prefix).remove_site_ip_restrict_info(site_name)
    # 历史配置文件
    ConfigMgr(site_name=site_name, config_prefix=config_prefix).clear_history_file()
    # 默认站点
    d_site_name, d_prefix = get_default_site()
    if d_site_name == site_name and d_prefix == config_prefix:
        d_file = "/www/server/panel/data/mod_default_site.pl"
        f = open(d_file, mode="w+")
        json.dump({"name": None, "prefix": None}, f)

    # 日志格式配置记录
    RealLogMgr(conf_prefix=config_prefix).remove_site_log_format_info(site_name)

    # 伪静态
    rewrite_path = "/www/server/panel/vhost/rewrite/{}{}.conf".format(config_prefix, site_name)
    if os.path.isdir(rewrite_path):
        os.remove(rewrite_path)
