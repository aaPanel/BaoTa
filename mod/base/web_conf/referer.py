import os
import re
import json
from dataclasses import dataclass
from typing import Tuple, Optional, Union, Dict
from .util import webserver, check_server_config, DB, \
    write_file, read_file, GET_CLASS, service_reload, pre_re_key
from mod.base import json_response
import public


@dataclass
class _RefererConf:
    name: str
    fix: str
    domains: str
    status: str
    return_rule: str
    http_status: str

    def __str__(self):
        return json.dumps(self.to_dict())

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "fix": self.fix,
            "domains": self.domains,
            "status": self.status,
            "http_status": self.http_status,
            "return_rule": self.return_rule
        }


class RealReferer:
    _referer_conf_dir = '/www/server/panel/vhost/config'  # 防盗链配置
    _ng_referer_conf_format = '''    #SECURITY-START 防盗链配置
    location ~ .*\.(%s)$ {
        expires      30d;
        access_log /dev/null;
        valid_referers %s;
        if ($invalid_referer){
           %s;
        }
    }
    #SECURITY-END'''

    def __init__(self, config_prefix: str):
        if not os.path.isdir(self._referer_conf_dir):
            os.makedirs(self._referer_conf_dir)
        self.config_prefix: str = config_prefix
        self._webserver = None

    @property
    def webserver(self) -> str:
        if self._webserver is not None:
            return self._webserver
        self._webserver = webserver()
        return self._webserver

    def get_config(self, site_name: str) -> Optional[_RefererConf]:
        try:
            config = json.loads(
                read_file("{}/{}{}_door_chain.json".format(self._referer_conf_dir, self.config_prefix, site_name)))
        except (json.JSONDecodeError, TypeError, ValueError):
            config = None
        if isinstance(config, dict):
            return _RefererConf(**config)
        return None

    def save_config(self, site_name: str, data: Union[dict, str, _RefererConf]) -> bool:
        if isinstance(data, dict):
            c = json.dumps(data)
        elif isinstance(data, _RefererConf):
            c = str(data)
        else:
            c = data

        file_path = "{}/{}{}_door_chain.json".format(self._referer_conf_dir, self.config_prefix, site_name)
        return write_file(file_path, c)

    # 检测参数，如果正确则返回 配置数据类型的值，否则返回错误信息
    @staticmethod
    def check_args(get: Union[Dict, GET_CLASS]) -> Union[_RefererConf, str]:
        res = {}
        if isinstance(get, GET_CLASS):
            try:
                res["status"] = "true" if not hasattr(get, "status") else get.status.strip()
                res["http_status"] = "false" if not hasattr(get, "http_status") else get.http_status.strip()
                res["name"] = get.site_name.strip()
                res["fix"] = get.fix.strip()
                res["domains"] = get.domains.strip()
                res["return_rule"] = get.return_rule.strip()
            except AttributeError:
                return "参数错误"
        else:
            try:
                res["status"] = "true" if "status" not in get else get["status"].strip()
                res["http_status"] = "false" if "http_status" not in get else get["http_status"].strip()
                res["name"] = get["site_name"].strip()
                res["fix"] = get["fix"].strip()
                res["domains"] = get["domains"].strip()
                res["return_rule"] = get["return_rule"].strip()
            except KeyError:
                return "参数错误"

        rconf = _RefererConf(**res)
        if rconf.status not in ("true", "false") and rconf.http_status not in ("true", "false"):
            return "状态参数只能使用【true,false】"
        if rconf.return_rule not in ('404', '403', '200', '301', '302', '401') and rconf.return_rule[0] != "/":
            return "响应资源应使用URI路径或HTTP状态码，如：/test.png 或 404"
        if len(rconf.domains) < 3:
            return "防盗链域名不能为空"
        rconf.domains = ",".join(
            set(filter(lambda x: x if x else None, map(lambda x: x.strip(), rconf.domains.split(",")))))
        if len(rconf.fix) < 2:
            return 'URL后缀不能为空!'
        return rconf

    def set_referer_security(self, rc: _RefererConf) -> Tuple[bool, str]:
        error_msg = self._set_nginx_referer_security(rc)
        if error_msg and self.webserver == "nginx":
            return False, error_msg
        error_msg = self._set_apache_referer_security(rc)
        if error_msg and self.webserver == "apache":
            return False, error_msg
        service_reload()
        self.save_config(rc.name, rc)
        return True, "设置成功"

    def _set_nginx_referer_security(self, rc: _RefererConf) -> Optional[str]:
        ng_file = '/www/server/panel/vhost/nginx/{}{}.conf'.format(self.config_prefix, rc.name)
        ng_conf = read_file(ng_file)
        if not isinstance(ng_conf, str):
            return "nginx配置文件丢失，无法设置"
        start_idx, end_idx = self._get_nginx_referer_security_idx(ng_conf)
        if rc.status == "true":
            if rc.return_rule[0] == "/":
                return_rule = "rewrite /.* {} break".format(rc.return_rule)
            else:
                return_rule = 'return {}'.format(rc.return_rule)

            valid_args_list = []
            if rc.http_status == "true":
                valid_args_list.extend(("none", "blocked"))
            valid_args_list.extend(map(lambda x: x.strip(), rc.domains.split(",")))
            valid_args = " ".join(valid_args_list)

            location_args = "|".join(map(lambda x: pre_re_key(x.strip()), rc.fix.split(",")))
            if start_idx is not None:
                new_conf = ng_conf[:start_idx] + "\n" + (
                        self._ng_referer_conf_format % (location_args, valid_args, return_rule)
                ) + "\n" + ng_conf[end_idx:]
            else:
                rep_redirect_include = re.compile(r"\sinclude +.*/redirect/.*\*\.conf;", re.M)
                redirect_include_res = rep_redirect_include.search(ng_conf)
                if redirect_include_res:
                    new_conf = ng_conf[:redirect_include_res.end()] + "\n" + (
                            self._ng_referer_conf_format % (location_args, valid_args, return_rule)
                    ) + ng_conf[redirect_include_res.end():]
                else:
                    if "#SSL-END" not in ng_conf:
                        return "添加配置失败，无法定位SSL相关配置的位置"

                    new_conf = ng_conf.replace("#SSL-END", "#SSL-END\n" + self._ng_referer_conf_format % (
                        location_args, valid_args, return_rule), 1)

        else:
            if start_idx is None:
                return None
            new_conf = ng_conf[:start_idx] + "\n" + ng_conf[end_idx:]

        write_file(ng_file, new_conf)
        if self.webserver == "nginx" and check_server_config() is not None:
            write_file(ng_file, ng_conf)
            return "配置失败"

    # 获取nginx防盗链配置的起始和结束位置
    @staticmethod
    def _get_nginx_referer_security_idx(ng_conf: str) -> Tuple[Optional[int], Optional[int]]:
        rep_security = re.compile(
            r"(\s*#\s*SECURITY-START.*\n)?\s*location\s+~\s+\.\*\\\.\(.*(\|.*)?\)\$\s*\{[^}]*valid_referers\s+[^;]*;"
        )
        res = rep_security.search(ng_conf)
        if res is None:
            return None, None

        start_idx = res.start()
        s_idx = start_idx + ng_conf[start_idx:].find("{") + 1  # 起始位置

        # 手动跟踪大括号层级，忽略注释内的括号
        max_idx = len(ng_conf)
        level = 1
        in_annotation = False
        while s_idx < max_idx and level > 0:
            current_char = ng_conf[s_idx]
            if current_char == '#' and not in_annotation:
                in_annotation = True
            if current_char == '\n':
                in_annotation = False
            if current_char == '{' and not in_annotation:
                level += 1
            elif current_char == '}' and not in_annotation:
                level -= 1
            s_idx += 1

        rep_comment = re.search(r"^\s*#\s*SECURITY-END[^\n]*\n", ng_conf[s_idx:])
        if rep_comment is not None:
            end_idx = s_idx + rep_comment.end()
        else:
            end_idx = s_idx

        return start_idx, end_idx

    @staticmethod
    def _build_apache_referer_security_conf(rc: _RefererConf) -> str:
        r_conf_list = ["    #SECURITY-START 防盗链配置", "    RewriteEngine on"]
        cond_format = "    RewriteCond %{{HTTP_REFERER}} !{} [NC]"
        if rc.http_status == "true":
            r_conf_list.append(cond_format.format("^$"))

        r_conf_list.extend(map(lambda x: cond_format.format(x.strip()), rc.domains.split(",")))

        rule_format = "    RewriteRule .({}) {} "
        if rc.return_rule[0] == "/":
            r_conf_list.append(rule_format.format(
                "|".join(map(lambda x: x.strip(), rc.fix.split(","))),
                rc.return_rule
            ))
        else:
            r_conf_list.append(rule_format.format(
                "|".join(map(lambda x: x.strip(), rc.fix.split(","))),
                "/{s}.html [R={s},NC,L]".format(s=rc.return_rule)
            ))

        r_conf_list.append("    #SECURITY-END")

        return "\n".join(r_conf_list)

    # 根据配置正则确定位置 并将配置文件添加进去 use_start 参数指定添加的前后
    def _add_apache_referer_security_by_rep_idx(self,
                                                rep: re.Pattern,
                                                use_start: bool,
                                                ap_conf, ap_file, r_conf) -> bool:
        tmp_conf_list = []
        last_idx = 0
        for tmp in rep.finditer(ap_conf):
            tmp_conf_list.append(ap_conf[last_idx:tmp.start()])
            if use_start:
                tmp_conf_list.append("\n" + r_conf + "\n")
                tmp_conf_list.append(tmp.group())
            else:
                tmp_conf_list.append(tmp.group())
                tmp_conf_list.append("\n" + r_conf + "\n")
            last_idx = tmp.end()
        if last_idx == 0:
            return False

        tmp_conf_list.append(ap_conf[last_idx:])
        _conf = "".join(tmp_conf_list)
        write_file(ap_file, _conf)
        if self.webserver == "apache" and check_server_config() is not None:
            write_file(ap_file, ap_conf)
            return False
        return True

    def _set_apache_referer_security(self, rc: _RefererConf) -> Optional[str]:
        ap_file = '/www/server/panel/vhost/apache/{}{}.conf'.format(self.config_prefix, rc.name)
        ap_conf = read_file(ap_file)
        if not isinstance(ap_conf, str):
            return "apache配置文件丢失，无法设置"
        rep_security = re.compile(r"(\n[ \t]*#\s*SECURITY-START.*)?\n"  # 前缀注释
                                  r"[ \t]*RewriteEngine[ \t]+on[ \t]*\n"  # 启用路由重写
                                  r"([ \t]*RewriteCond[ \t]+%\{HTTP_REFERER}[^\n]+\n)*"  # 配置REFERER规则
                                  r"[ \t]*RewriteRule[^\n]*"  # 重写路由
                                  r"(\n[ \t]*#[ \t]*SECURITY-END.*)?")  # 后缀注释

        res = rep_security.search(ap_conf)
        # public.print_log(res.group())
        if rc.status == "true":
            r_conf = self._build_apache_referer_security_conf(rc)
            if res is not None:
                new_conf_list = []
                _idx = 0
                for tmp_res in rep_security.finditer(ap_conf):
                    new_conf_list.append(ap_conf[_idx:tmp_res.start()])
                    new_conf_list.append("\n" + r_conf)
                    _idx = tmp_res.end()
                new_conf_list.append(ap_conf[_idx:])
                new_conf = "".join(new_conf_list)
                write_file(ap_file, new_conf)
                if self.webserver == "apache" and check_server_config() is not None:
                    write_file(ap_file, ap_conf)
                    return "配置修改失败"
                return None
            else:
                rep_redirect_include = re.compile(r"IncludeOptional +.*/redirect/.*\*\.conf.*\n", re.M)
                rep_custom_log = re.compile(r"CustomLog .*\n")
                rep_deny_files = re.compile(r"\n\s*#DENY FILES")
                if self._add_apache_referer_security_by_rep_idx(rep_redirect_include, False, ap_conf, ap_file, r_conf):
                    return None
                if self._add_apache_referer_security_by_rep_idx(rep_custom_log, False, ap_conf, ap_file, r_conf):
                    return None
                if self._add_apache_referer_security_by_rep_idx(rep_deny_files, True, ap_conf, ap_file, r_conf):
                    return None
                return "设置添加失败"

        else:
            if res is None:
                return None

            new_conf_list = []
            _idx = 0
            for tmp_res in rep_security.finditer(ap_conf):
                new_conf_list.append(ap_conf[_idx:tmp_res.start()])
                _idx = tmp_res.end()
            new_conf_list.append(ap_conf[_idx:])
            new_conf = "".join(new_conf_list)
            write_file(ap_file, new_conf)
            if self.webserver == "apache" and check_server_config() is not None:
                write_file(ap_file, ap_conf)
                return "配置修改失败"
            return None

    def get_referer_security(self, site_name) -> Optional[dict]:
        r = self.get_config(site_name)
        if r is None:
            tmp = self._get_referer_security_by_conf(site_name)
            if isinstance(tmp, dict):
                return tmp
            return None

        return r.to_dict()

    def remove_site_referer_info(self, site_name):
        file_path = "{}/{}{}_door_chain.json".format(self._referer_conf_dir, self.config_prefix, site_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    # 从配置文件中获取referer配置信息
    # 暂时不实现，意义不大
    def _get_referer_security_by_conf(self, site_name: str) -> Optional[dict]:
        if self.webserver == "nginx":
            return self._get_nginx_referer_security(site_name)
        else:
            return self._get_apache_referer_security(site_name)

    def _get_nginx_referer_security(self, site_name: str) -> Optional[dict]:
        ng_file = '/www/server/panel/vhost/nginx/{}{}.conf'.format(self.config_prefix, site_name)
        ng_conf = read_file(ng_file)
        if not isinstance(ng_conf, str):
            return None

        start_idx, end_idx = self._get_nginx_referer_security_idx(ng_conf)
        if not start_idx or not end_idx:
            return None
        re_data = {
            "fix": "jpg,jpeg,gif,png,js,css",
            "domains": "",
            "status": False,
            "return_rule": "404",
            "http_status": False,
        }
        referer_conf = ng_conf[start_idx:end_idx]
        regexp_suffix = re.compile(r"\.\*\\\.\((?P<suffix>([^|)\s]+\|)*[^|\s)]+)\)\$\s*\{[^}]*valid_referers")
        regexp_valid = re.compile(r"\n[ \t]*valid_referers\s+(?P<domain>[^;]*)\s*;")
        regexp_return = re.compile(r"\n[ \t]*if\s*\(\s*\$invalid_referer\s*\)\s*{\s*(?P<target>[^;]+;)\s*}")

        suffix = regexp_suffix.search(referer_conf)
        if suffix is not None:
            re_data["status"] = True
            fix = suffix.group("suffix")
            re_data["fix"] = fix.strip("|")

        domain = regexp_valid.search(referer_conf)
        if domain is not None:
            re_data["status"] = True
            domains = domain.group("domain")
            domains_list = domains.split()
            if "none" in domains_list or "blocked" in domains_list:
                re_data["http_status"] = True
                domains_list = [i for i in domains_list if i not in ("none", "blocked")]
            re_data["domains"] = ",".join(domains_list)

        return_rule = regexp_return.search(referer_conf)
        if return_rule is not None:
            return_rule = return_rule.group("target")
            if return_rule.startswith("return "):
                return_rule = return_rule[7:]
            re_data["return_rule"] = return_rule
            if return_rule.startswith("return "):
                re_data["return_rule"] = return_rule[7:]
            elif return_rule.startswith("rewrite "):
                tmp = return_rule.split()
                re_data["return_rule"] = tmp[2]

        return re_data

    def _get_apache_referer_security(self, site_name: str) -> Optional[dict]:
        ap_file = '/www/server/panel/vhost/apache/{}{}.conf'.format(self.config_prefix, site_name)
        ap_conf = read_file(ap_file)
        if not isinstance(ap_conf, str):
            return None
        rep_security = re.compile(r"(\n[ \t]*#\s*SECURITY-START.*)?\n"  # 前缀注释
                                  r"[ \t]*RewriteEngine[ \t]+on[ \t]*\n"  # 启用路由重写
                                  r"([ \t]*RewriteCond[ \t]+%\{HTTP_REFERER}[^\n]+\n)*"  # 配置REFERER规则
                                  r"[ \t]*RewriteRule[^\n]*"  # 重写路由
                                  r"(\n[ \t]*#[ \t]*SECURITY-END.*)?")  # 后缀注释

        security_conf = rep_security.search(ap_conf)
        if security_conf is None:
            return None
        security_conf = security_conf.group()
        regexp_suffix = re.compile(
            r'\n[ \t]*RewriteRule[^(]*\((?P<fix>([^|)\s]+\|)*[^|\s)]+)\)\s(?P<rule>\S+)(?P<code>\s+\[R=\d+,NC,L])?')
        regexp_domain = re.compile(r'\n[ \t]*RewriteCond[ \t]+%\{HTTP_REFERER}[ \t]+!(?P<domain>\S+)\s+\[NC]')
        re_data = {
            "fix": "jpg,jpeg,gif,png,js,css",
            "domains": "",
            "status": False,
            "return_rule": "404",
            "http_status": False,
        }
        suffix = regexp_suffix.search(security_conf)
        if suffix is not None:
            re_data["status"] = True
            fix = suffix.group("fix")
            rule = suffix.group("rule")
            code = suffix.group("code")
            if code:
                rule = rule.lstrip("/")[:3]
            fix = fix.replace("|", ",")
            re_data["fix"] = fix
            re_data["return_rule"] = rule

        domain_list = []
        for tmp in regexp_domain.finditer(security_conf):
            re_data["status"] = True
            domain = tmp.group("domain")
            if domain.startswith("!"):
                domain = domain[1:]
            if domain == "^$":
                re_data["http_status"] = True
                continue
            domain_list.append(domain)

        re_data["domains"] = ",".join(domain_list)
        return re_data


class Referer:

    def __init__(self, config_prefix: str):
        self.config_prefix: str = config_prefix
        self._r = RealReferer(self.config_prefix)

    def get_referer_security(self, get):
        try:
            site_name = get.site_name.strip()
        except AttributeError:
            return json_response(status=False, msg="参数错误")

        data = self._r.get_referer_security(site_name)
        if data is None:
            default_conf = {
                "name": site_name,
                "fix": "jpg,jpeg,gif,png,js,css",
                "domains": "",
                "status": False,
                "return_rule": "404",
                "http_status": False,
            }
            site_info = DB("sites").where("name=?", (site_name,)).field('id').find()
            if not isinstance(site_info, dict):
                return json_response(status=False, msg="站点查询错误")
            domains_info = DB("domain").where("pid=?", (site_info["id"],)).field('name').select()
            if not isinstance(domains_info, list):
                return json_response(status=False, msg="站点查询错误")

            default_conf["domains"] = ",".join(map(lambda x: x["name"], domains_info))
            return json_response(status=True, data=default_conf)

        if isinstance(data["status"], str):
            data["status"] = True if data["status"] == "true" else False
        if isinstance(data["http_status"], str):
            data["http_status"] = True if data["http_status"] == "true" else False

        return json_response(status=True, data=data)

    def set_referer_security(self, get):
        r = self._r.check_args(get)
        if isinstance(r, str):
            return json_response(status=False, msg=r)

        flag, msg = self._r.set_referer_security(r)
        return json_response(status=flag, msg=msg)
