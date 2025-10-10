import os
import re
import json
from typing import Tuple, Optional, Union
from ipaddress import ip_address

from .util import webserver, check_server_config, write_file, read_file, DB, service_reload
from mod.base import json_response


class _BaseRestrict:
    def __init__(self, config_file: str, site_name: str):
        self._conf_file = config_file
        self._conf = self._read_conf()
        self.site_name = site_name

    def _read_conf(self):
        default_conf = {
                "restrict_type": "closed", 
                "black_list": [],
                "white_list": []
            }
        
        if not os.path.exists(self._conf_file):
            return default_conf
        try:
            conf = json.loads(read_file(self._conf_file))
        except:
            conf = default_conf
        return conf

    def to_view(self):
        return self._conf


class _IpRestrict(_BaseRestrict):
    def __init__(self, site_name: str, config_prefix: str):
        setup_path = "/www/server/panel"
        ip_restrict_conf_dir = "{}/data/ip_restrict_data".format(setup_path)
        if not os.path.exists(ip_restrict_conf_dir):
            os.makedirs(ip_restrict_conf_dir)
        super().__init__("{}/{}{}".format(ip_restrict_conf_dir, config_prefix, site_name), site_name)
        self.config_prefix = config_prefix
        self.nginx_sub_file = "{}/vhost/ip-restrict/{}{}.conf".format(setup_path, self.config_prefix, self.site_name)

    @property
    def restrict_type(self):
        return self._conf.get("restrict_type", "black")

    @restrict_type.setter
    def restrict_type(self, data: str):
        if data in ("black", "white", "closed"):
            self._conf["restrict_type"] = data

    @property
    def black_list(self):
        return self._conf.get("black_list", [])

    @black_list.setter
    def black_list(self, list_data: list):
        self._conf["black_list"] = list_data

    @property
    def white_list(self):
        return self._conf.get("white_list", [])

    @white_list.setter
    def white_list(self, list_data: list):
        self._conf["white_list"] = list_data

    def save(self) -> Tuple[bool, str]:
        if not self._conf:  # 没有的时候不操作
            return True, "操作成功"
        write_file(self._conf_file, json.dumps(self._conf))

        if self.restrict_type == "closed":
            write_file(self.nginx_sub_file, "")
            service_reload()
            return True, "操作成功"

        tmp_conf = []
        if self.restrict_type == "white":
            for i in self.white_list:
                tmp_conf.append("allow {};".format(i))

            tmp_conf.append("deny all; # 除开上述IP外，其他IP全部禁止访问")
        elif self.restrict_type == "black":
            for i in self.black_list:
                tmp_conf.append("deny {};".format(i))
        else:
            raise ValueError("错误的类型，无法操作")

        write_file(self.nginx_sub_file, "\n".join(tmp_conf))
        error_msg = check_server_config()
        if error_msg is not None:
            write_file(self.nginx_sub_file, "")
            return False, "操作失败"
        service_reload()
        return True, "操作成功"

    # 删除网站时调用，删除配置文件
    def remove_config_for_remove_site(self):
        if os.path.isfile(self.nginx_sub_file):
            os.remove(self.nginx_sub_file)

        if os.path.isfile(self._conf_file):
            os.remove(self._conf_file)


class RealIpRestrict:

    def __init__(self, config_prefix: str = ""):
        self.config_prefix = config_prefix
        self.web_server = webserver()

    # 获取某个站点的IP黑白名单详情
    def restrict_conf(self, site_name: str) -> Tuple[bool, Union[str, dict]]:
        if self.web_server != "nginx":
            return False, "不支持除nginx之外的服务器"
        ip_conf = _IpRestrict(site_name, self.config_prefix)
        if not self._get_status_in_nginx_conf(ip_conf):
            ip_conf.restrict_type = "closed"
        return True, ip_conf.to_view()

    # 从配置文件中获取状态
    def _get_status_in_nginx_conf(self, ip_conf: _IpRestrict) -> bool:
        setup_path = "/www/server/panel"
        ng_file = "{}/vhost/nginx/{}{}.conf".format(setup_path, self.config_prefix, ip_conf.site_name)
        rep_include = re.compile(r"\sinclude +.*/ip-restrict/.*\.conf;", re.M)
        ng_conf = read_file(ng_file)
        if not isinstance(ng_conf, str):
            return False
        if rep_include.search(ng_conf):
            return True
        return False

    def _set_nginx_include(self, ip_conf: _IpRestrict) -> Tuple[bool, str]:
        setup_path = "/www/server/panel"
        ng_file = "{}/vhost/nginx/{}{}.conf".format(setup_path, self.config_prefix, ip_conf.site_name)
        if not os.path.exists(os.path.dirname(ip_conf.nginx_sub_file)):
            os.makedirs(os.path.dirname(ip_conf.nginx_sub_file), 0o600)
        if not os.path.isfile(ip_conf.nginx_sub_file):
            write_file(ip_conf.nginx_sub_file, "")

        ng_conf = read_file(ng_file)
        if not isinstance(ng_conf, str):
            return False, "nginx配置文件读取失败"

        rep_include = re.compile(r"\s*include\s+.*/ip-restrict/.*\.conf;", re.M)
        if rep_include.search(ng_conf):
            return True, ""

        _include_str = (
            "\n    #引用IP黑白名单规则，注释后配置的IP黑白名单将无效\n"
            "    include {};"
        ).format(ip_conf.nginx_sub_file)

        rep_redirect_include = re.compile(r"\s*include\s+.*/redirect/.*\.conf;", re.M)  # 如果有重定向，添加到重定向之后
        redirect_include_res = rep_redirect_include.search(ng_conf)
        if redirect_include_res:
            new_conf = ng_conf[:redirect_include_res.end()] + _include_str + ng_conf[redirect_include_res.end():]
        else:
            if "#SSL-END" not in ng_conf:
                return False, "添加配置失败，无法定位SSL相关配置的位置"

            new_conf = ng_conf.replace("#SSL-END", "#SSL-END" + _include_str)
        write_file(ng_file, new_conf)
        if self.web_server == "nginx" and check_server_config() is not None:
            write_file(ng_file, ng_conf)
            return False, "添加配置失败"

        return True, ""

    def set_ip_restrict(self, site_name: str, set_type: str) -> Tuple[bool, str]:
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        if set_type not in ("black", "white", "closed"):
            return False, "不支持的类型【{}】".format(set_type)
        ip_restrict.restrict_type = set_type
        f, msg = self._set_nginx_include(ip_restrict)
        if not f:
            return False, msg

        return ip_restrict.save()

    def add_black_ip_restrict(self, site_name: str, *ips: str) -> Tuple[bool, str]:
        try:
            for ip in ips:
                _ = ip_address(ip)  # 引发valueError
        except ValueError:
            return False, "ip参数解析错误"
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        black_list = ip_restrict.black_list
        for i in ips:
            if i not in black_list:
                black_list.append(i)

        ip_restrict.black_list = black_list
        f, msg = self._set_nginx_include(ip_restrict)
        if not f:
            return False, msg

        return ip_restrict.save()

    def remove_black_ip_restrict(self, site_name: str, *ips: str):
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        black_list = ip_restrict.black_list
        for i in ips:
            if i in black_list:
                black_list.remove(i)

        ip_restrict.black_list = black_list
        f, msg = self._set_nginx_include(ip_restrict)
        if not f:
            return False, msg

        return ip_restrict.save()

    def add_white_ip_restrict(self, site_name: str, *ips: str) -> Tuple[bool, str]:
        try:
            for ip in ips:
                _ = ip_address(ip)  # 引发valueError
        except ValueError:
            return False, "ip参数解析错误"
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        white_list = ip_restrict.white_list
        for i in ips:
            if i not in white_list:
                white_list.append(i)

        ip_restrict.white_list = white_list
        f, msg = self._set_nginx_include(ip_restrict)
        if not f:
            return False, msg

        return ip_restrict.save()

    def remove_white_ip_restrict(self, site_name: str, *ips: str) -> Tuple[bool, str]:
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        white_list = ip_restrict.white_list
        for i in ips:
            if i in white_list:
                white_list.remove(i)

        ip_restrict.white_list = white_list

        return ip_restrict.save()

    def remove_site_ip_restrict_info(self, site_name: str):
        ip_restrict = _IpRestrict(site_name, self.config_prefix)
        ip_restrict.remove_config_for_remove_site()


class IpRestrict:

    def __init__(self, config_prefix: str = ""):
        self.config_prefix = config_prefix
        self._ri = RealIpRestrict(self.config_prefix)

    # 获取ip控制信息
    def restrict_conf(self, get):
        try:
            site_name = get.site_name.strip()
        except (AttributeError, json.JSONDecodeError):
            return json_response(status=False, msg="参数错误")

        f, d = self._ri.restrict_conf(site_name)
        if not f:
            return json_response(status=f, msg=d)
        return json_response(status=f, data=d)

    # 设置ip黑白名单状态
    def set_ip_restrict(self, get):
        try:
            site_name = get.site_name.strip()
            set_ip_restrict = get.set_type.strip()
        except (AttributeError, json.JSONDecodeError):
            return json_response(status=False, msg="参数错误")

        f, m = self._ri.set_ip_restrict(site_name, set_ip_restrict)
        return json_response(status=f, msg=m)

    # 添加黑名单
    def add_black_ip_restrict(self, get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        f, m = self._ri.add_black_ip_restrict(site_name, value)
        return json_response(status=f, msg=m)

    # 移除黑名单
    def remove_black_ip_restrict(self, get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except (AttributeError, json.JSONDecodeError):
            return json_response(status=False, msg="参数错误")

        f, m = self._ri.remove_black_ip_restrict(site_name, value)
        return json_response(status=f, msg=m)

    # 添加白名单
    def add_white_ip_restrict(self, get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except (AttributeError, json.JSONDecodeError):
            return json_response(status=False, msg="参数错误")

        f, m = self._ri.add_white_ip_restrict(site_name, value)
        return json_response(status=f, msg=m)

    # 移除白名单
    def remove_white_ip_restrict(self, get):
        try:
            site_name = get.site_name.strip()
            value = get.value.strip()
        except (AttributeError, json.JSONDecodeError):
            return json_response(status=False, msg="参数错误")

        f, m = self._ri.remove_white_ip_restrict(site_name, value)
        return json_response(status=f, msg=m)


