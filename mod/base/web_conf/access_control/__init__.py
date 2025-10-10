import os
from .base import web_type, BaseCorsManager
from .nginx_cors_manager import NginxConfigManager, NginxLuaConfigManager
from .apache_cors_manager import ApacheConfigManager
from typing import Union

def cors_manager(site_name: str, site_type: str) -> Union[BaseCorsManager, str]:
    if site_type.lower() in ["php", "proxy", "docker", "wp2"]:
        config_path = "/www/server/panel/vhost/%s/{}.conf".format(site_name)
    else:
        config_path = "/www/server/panel/vhost/%s/{}_{}.conf".format(site_type.lower(), site_name)

    if web_type() == 'nginx':
        config_path = config_path % "nginx"
        if not os.path.exists(config_path):
            return "没服务配置文件，可能是未开启外网映射或配置文件丢失"
        if NginxConfigManager.can_use_lua_module():
            return NginxLuaConfigManager(config_path)
        return NginxConfigManager(config_path)
    elif web_type() == 'apache':
        config_path = config_path % "apache"
        if not os.path.exists(config_path):
            return "没服务配置文件，可能是未开启外网映射或配置文件丢失"
        return ApacheConfigManager(config_path)
    else:
        return "不支持的web服务，目前支持使用Nginx或Apache"

__all__ = [
    'NginxConfigManager',
    'ApacheConfigManager',
    "NginxLuaConfigManager",
    'cors_manager',
    "BaseCorsManager",
]


