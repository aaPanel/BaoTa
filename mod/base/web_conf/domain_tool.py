import os
import re
from typing import Tuple, Optional, Union, List, Dict

from .util import webserver, check_server_config, write_file, read_file, service_reload, listen_ipv6, use_http2


def domain_to_puny_code(domain: str) -> str:
    new_domain = ''
    for dkey in domain.split('.'):
        if dkey == '*' or dkey == "":
            continue
        # 匹配非ascii字符
        match = re.search(u"[\x80-\xff]+", dkey)
        if not match:
            match = re.search(u"[\u4e00-\u9fa5]+", dkey)
        if not match:
            new_domain += dkey + '.'
        else:
            new_domain += 'xn--' + dkey.encode('punycode').decode('utf-8') + '.'
    if domain.startswith('*.'):
        new_domain = "*." + new_domain
    return new_domain[:-1]


def check_domain(domain: str) -> Optional[str]:
    domain = domain_to_puny_code(domain)
    # 判断通配符域名格式
    if domain.find('*') != -1 and domain.find('*.') == -1:
        return None

    # 判断域名格式
    rep_domain = re.compile(r"^([\w\-*]{1,100}\.){1,24}([\w\-]{1,24}|[\w\-]{1,24}\.[\w\-]{1,24})$")
    if not rep_domain.match(domain):
        return None
    return domain


def is_domain(domain: str) -> bool:
    domain_regex = re.compile(
        r'(?:[A-Z0-9_](?:[A-Z0-9-_]{0,247}[A-Z0-9])?\.)+(?:[A-Z]{2,6}|[A-Z0-9-]{2,}(?<!-))\Z',
        re.IGNORECASE
    )
    return True if domain_regex.match(domain) else False


# 检查原始的域名列表，返回[(domain, port)] 的格式，并返回其中有错误的项目
def normalize_domain(*domains: str) -> Tuple[List[Tuple[str, str]], List[Dict]]:
    res, error = [], []
    for i in domains:
        if not i.strip():
            continue
        d_list = [i.strip() for i in i.split(":")]
        if len(d_list) > 1:
            try:
                p = int(d_list[1])
                if not (1 < p < 65535):
                    error.append({
                        "domain": i,
                        "msg": "端口范围错误"
                    })
                    continue
                else:
                    d_list[1] = str(p)
            except:
                error.append({
                    "domain": i,
                    "msg": "端口范围错误"
                })
                continue
        else:
            d_list.append("80")
        d, p = d_list
        d = check_domain(d)
        if isinstance(d, str):
            res.append((d, p)),
            continue
        error.append({
            "domain": i,
            "msg": "域名格式错误"
        })

    res = list(set(res))
    return res, error


class NginxDomainTool:
    ng_vhost = "/www/server/panel/vhost/nginx"

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix

    # 在给定的配置文件中添加端口
    @staticmethod
    def nginx_add_port_by_config(conf, *port: str, is_http3=False) -> str:
        ports = set()
        for p in port:
            ports.add(p)

        # 设置端口
        rep_port = re.compile(r"\s*listen\s+[\[\]:]*(?P<port>[0-9]+)(?P<ds>\s*default_server)?.*;[^\n]*\n", re.M)
        use_ipv6 = listen_ipv6()
        last_port_idx = None
        need_remove_port_idx = []
        had_ports = set()
        is_default_server = False
        for tmp_res in rep_port.finditer(conf):
            last_port_idx = tmp_res.end()
            if tmp_res.group("ds") and tmp_res.group("ds").strip():
                is_default_server = True
            if tmp_res.group("port") in ports:
                had_ports.add(tmp_res.group("port"))
            elif tmp_res.group("port") != "443":
                need_remove_port_idx.append((tmp_res.start(), tmp_res.end()))

        if not last_port_idx:
            last_port_idx = re.search(r"server\s*\{\s*?\n", conf).end()

        need_add_ports = ports - had_ports
        d_s = " default_server" if is_default_server else ""
        h2 = " http2" if use_http2() else ""
        if need_add_ports or is_http3:
            listen_add_list = []
            for p in need_add_ports:
                if p == "443":
                    tmp = "    listen 443 ssl{}{};\n".format(h2, d_s)
                    if use_ipv6:
                        tmp += "    listen [::]:443 ssl{}{};\n".format(h2, d_s)
                    listen_add_list.append(tmp)
                    continue

                tmp = "    listen {}{};\n".format(p, d_s)
                if use_ipv6:
                    tmp += "    listen [::]:{}{};\n".format(p, d_s)
                listen_add_list.append(tmp)

            if is_http3 and "443" in (had_ports | had_ports):
                listen_add_list.append("    listen 443 quic{};\n".format(d_s))
                if use_ipv6:
                    listen_add_list.append("    listen [::]:443 quic{};\n".format(d_s))

            new_conf = conf[:last_port_idx] + "".join(listen_add_list) + conf[last_port_idx:]
            return new_conf
        return conf

    # 将站点配置的域名和端口，写到配置文件中
    def nginx_set_domain(self, site_name, *domain: Tuple[str, str]) -> Optional[str]:
        ng_file = '{}/{}{}.conf'.format(self.ng_vhost, self.conf_prefix, site_name)
        ng_conf = read_file(ng_file)
        if not ng_conf:
            return "nginx配置文件丢失"

        domains_set, ports = set(), set()
        for d, p in domain:
            domains_set.add(d)
            ports.add(p)

        # 设置域名
        rep_server_name = re.compile(r"\s*server_name\s*(.*);", re.M)
        new_conf = rep_server_name.sub("\n    server_name {};".format(" ".join(domains_set)), ng_conf, 1)

        # 设置端口
        rep_port = re.compile(r"\s*listen\s+[\[\]:]*(?P<port>[0-9]+)(?P<ds>\s*default_server)?.*;[^\n]*\n", re.M)
        use_ipv6 = listen_ipv6()
        last_port_idx = None
        need_remove_port_idx = []
        had_ports = set()
        is_default_server = False
        for tmp_res in rep_port.finditer(new_conf):
            last_port_idx = tmp_res.end()
            if tmp_res.group("ds") is not None and tmp_res.group("ds").strip():
                is_default_server = True
            if tmp_res.group("port") in ports:
                had_ports.add(tmp_res.group("port"))
            elif tmp_res.group("port") != "443":
                need_remove_port_idx.append((tmp_res.start(), tmp_res.end()))

        if not last_port_idx:
            last_port_idx = re.search(r"server\s*\{\s*?\n", new_conf).end()

        ports = ports - had_ports
        if ports:
            d_s = " default_server" if is_default_server else ""
            listen_add_list = []
            for p in ports:
                tmp = "    listen {}{};\n".format(p, d_s)
                if use_ipv6:
                    tmp += "    listen [::]:{}{};\n".format(p, d_s)
                listen_add_list.append(tmp)

            new_conf = new_conf[:last_port_idx] + "".join(listen_add_list) + new_conf[last_port_idx:]

        # 移除多余的port监听：
        # 所有遍历的索引都在 last_port_idx 之前，所有不会影响之前的修改 ↑
        if need_remove_port_idx:
            conf_list = []
            idx = 0
            for start, end in need_remove_port_idx:
                conf_list.append(new_conf[idx:start])
                idx = end
            conf_list.append(new_conf[idx:])
            new_conf = "".join(conf_list)

        # 保存配置文件
        write_file(ng_file, new_conf)
        web_server = webserver()
        if web_server == "nginx" and check_server_config() is not None:
            write_file(ng_file, ng_conf)
            return "配置失败"
        if web_server == "nginx":
            service_reload()


class ApacheDomainTool:
    ap_vhost = "/www/server/panel/vhost/apache"
    ap_path = "/www/server/apache"

    def __init__(self, conf_prefix: str = ""):
        self.conf_prefix = conf_prefix

    # 将站点配置的域名和端口，写到配置文件中
    def apache_set_domain(self,
                          site_name,  # 站点名称
                          *domain: Tuple[str, str],  # 域名列表，可以为多个
                          template_path: Optional[str] = None,  # 在新加端口时使用一个模板作为添加内容
                          template_kwargs: Optional[dict] = None,  # 在使用一个模板时的填充参数，
                          ) -> Optional[str]:
        """
        template_path: 在新加端口时使用一个模板作为添加内容
        template_kwargs: 在使用一个模板时的填充参数
                        port domains server_admin server_name 四个参数会自动生成并填充
        没有传入 template_path 将会复制第一个虚拟机（VirtualHost）配置
        """
        ap_file = '{}/{}{}.conf'.format(self.ap_vhost, self.conf_prefix, site_name)
        ap_conf: str = read_file(ap_file)
        if not ap_conf:
            return "nginx配置文件丢失"

        domains, ports = set(), set()
        for i in domain:
            domains.add(str(i[0]))
            ports.add(str(i[1]))

        domains_str = " ".join(domains)

        # 设置域名
        rep_server_name = re.compile(r"\s*ServerAlias\s*(.*)\n", re.M)
        new_conf = rep_server_name.sub("\n    ServerAlias {}\n".format(domains_str), ap_conf)

        tmp_template_res = re.search(r"<VirtualHost(.|\n)*?</VirtualHost>", new_conf)
        if not tmp_template_res:
            tmp_template = None
        else:
            tmp_template = tmp_template_res.group()

        rep_ports = re.compile(r"<VirtualHost +.*:(?P<port>\d+)+\s*>")
        need_remove_port = []
        for tmp in rep_ports.finditer(new_conf):
            if tmp.group("port") in ports:
                ports.remove(tmp.group("port"))
            elif tmp.group("port") != "443":
                need_remove_port.append(tmp.group("port"))

        if need_remove_port:
            for i in need_remove_port:
                tmp_rep = re.compile(r"<VirtualHost.*" + i + r"(.|\n)*?</VirtualHost[^\n]*\n?")
                new_conf = tmp_rep.sub("", new_conf, 1)

        if ports:
            other_config_body_list = []
            if template_path is not None:
                # 添加其他的port
                try:
                    config_body = read_file(template_path)
                    for p in ports:
                        other_config_body_list.append(config_body.format(
                            port=p,
                            server_admin="admin@{}".format(site_name),
                            server_name='{}.{}'.format(p, site_name),
                            domains=domains_str,
                            **template_kwargs
                        ))
                except:
                    raise ValueError("参数与模板不匹配")
            else:
                if tmp_template is None:
                    return "配置文件格式错误"

                for p in ports:
                    other_config_body_list.append(rep_ports.sub("<VirtualHost *:{}>".format(p), tmp_template, 1))

            new_conf += "\n" + "\n".join(other_config_body_list)
        from mod.base.web_conf import ap_ext
        new_conf = ap_ext.remove_extension_from_config(site_name, new_conf)
        new_conf = ap_ext.set_extension_by_config(site_name, new_conf)
        write_file(ap_file, new_conf)
        # 添加端口
        self.apache_add_ports(*ports)
        web_server = webserver()
        if web_server == "apache" and check_server_config() is not None:
            write_file(ap_file, ap_conf)
            return "配置失败"

        if web_server == "apache":
            service_reload()

    # 添加apache主配置文件中的端口监听
    @classmethod
    def apache_add_ports(cls, *ports: Union[str, int]) -> None:
        real_ports = set()
        for p in ports:
            real_ports.add(str(p))

        ssl_conf_file = '{}/conf/extra/httpd-ssl.conf'.format(cls.ap_path)
        if os.path.isfile(ssl_conf_file):
            ssl_conf = read_file(ssl_conf_file)
            if isinstance(ssl_conf, str) and ssl_conf.find('Listen 443') != -1:
                ssl_conf = ssl_conf.replace('Listen 443', '')
                write_file(ssl_conf_file, ssl_conf)

        ap_conf_file = '{}/conf/httpd.conf'.format(cls.ap_path)
        if not os.path.isfile(ap_conf_file):
            return
        ap_conf = read_file(ap_conf_file)
        if ap_conf is None:
            return

        rep_ports = re.compile(r"Listen\s+(?P<port>[0-9]+)\n", re.M)
        last_idx = None
        for key in rep_ports.finditer(ap_conf):
            last_idx = key.end()
            if key.group("port") in real_ports:
                real_ports.remove(key.group("port"))

        if not last_idx:
            return
        new_conf = ap_conf[:last_idx] + "\n".join(["Listen %s" % i for i in real_ports]) + "\n" + ap_conf[last_idx:]
        write_file(ap_conf_file, new_conf)
