import os.path
from typing import Callable

import psutil

from mod.project.node.dbutil import HttpNode, LoadSite, TcpNode
from mod.project.node.nodeutil import ServerNode, LocalNode
from .nginx_utils import NginxUtils
from .request_check import RequestChecker


def check_http_node(node:HttpNode, main_domain, log_call:Callable[[str], None]) -> str:
    srv = ServerNode.new_by_id(node.node_id)
    if not srv:
        return "无法连接到目标节点的机器"
    if srv.is_local:
        return _check_local_http_node(node, main_domain, log_call)

    if not node.node_site_id:
        log_call("负载服务节点：{}不存在，即将在目标机器创建网站！".format(node.node_site_name))
        site_id, err = srv.create_php_site(node.node_site_name, node.port)
        if err:
            return "无法在目标节点{}的机器创建网站：{}".format(srv.show_name(), err)

        node.node_site_id = site_id
        log_call("成功创建网站：{}".format(node.node_site_name))

    if srv and node.node_site_name != main_domain and main_domain!="" and not srv.has_domain(node.node_site_id, main_domain):
        log_call("负载服务节点：{}的域名与主域名不一致，即将把主域名添加至目标机器".format(node.node_site_name))
        flag, msg = srv.add_domain(node.node_site_id, node.node_site_name, main_domain, node.port)
        if not flag:
            return "无法在目标节点{}的机器更新域名".format(srv.show_name())
        log_call("成功更新域名：{}".format(node.node_site_name))

    log_call("开始检查负载服务节点：{}访问情况".format(node.node_site_name))
    if not RequestChecker.check_http_node(node):
        if node.port in (80, 443):
            return  "无法访问负载服务节点：{}".format(node.node_site_name)
        log_call("负载服务节点：{}访问失败，将尝试在目标机器放行防火墙端口".format(node.node_site_name))
        flag, msg = srv.set_firewall_open(node.port, "tcp")
        if not flag:
            return "无法在目标节点{}的机器放行端口：{}".format(srv.show_name(), node.port)
        if not RequestChecker.check_http_node(node):
            return "无法访问负载服务节点：{}".format(node.node_site_name)

    log_call("负载服务节点：{}访问成功".format(node.node_site_name))
    return ""


def _check_local_http_node(node:HttpNode, main_domain, log_call:Callable[[str], None]) -> str:
    srv = LocalNode()
    if main_domain != "" and main_domain == node.node_site_name:
        return "使用本机节点作为负载服务节点时，网站域名不能与主域名一致"
    if node.port in (80, 443):
        return "使用本机节点作为负载服务节点时，端口不能为80或443"
    if not node.node_site_id:
        log_call("负载服务节点：{}不存在，即将在本机创建网站！".format(node.node_site_name))
        site_id, err = srv.create_php_site(node.node_site_name, node.port, ps="负载均衡：{}【子站点】".format(main_domain))
        if err:
            return "无法在目标节点{}的机器创建网站：{}".format(srv.show_name(), err)

        node.node_site_id = site_id
        log_call("成功创建网站：{}".format(node.node_site_name))
    else:
        srv.add_domain(node.node_site_id, node.node_site_name, node.node_site_name, node.port)
    return ""


def check_http_load_data(load:LoadSite, log_call:Callable[[str], None]):
    if not load.site_id:
        log_call("主节点网站：{}不存在，即将在本机创建网站！".format(load.site_name))
        site_id, err = LocalNode().create_php_site(site_name=load.site_name, ps="负载均衡：{}【主站点】".format(load.ps))
        if err:
            return "无法在本机创建网站：{}".format(err)

        load.site_id = site_id

    if LocalNode.site_proxy_list(load.site_name):
        return "当前选择的主节点网站存在反向代理配置，无法为其设置负载均衡"
    if load.http_config["http_alg"] == "sticky_cookie":
        if not NginxUtils.has_sticky_module():
            return "负载均衡的cookie会话跟随，需要Nginx安装sticky-module模块，您可以尝试在【软件商店】更新、重装或切换Nginx版本"

def check_tcp_load_data(load: LoadSite, log_call: Callable[[str], None]) -> str:
    # 检查是否出现端口占用
    for conn in psutil.net_connections():
        if conn.status == 'LISTEN' and conn.laddr.port == load.tcp_config["port"]:
            pid = conn.pid
            if psutil.Process(pid).exe().find("nginx") == -1:
                return "端口{}被占用，请注意是否影响nginx启动".format(load.tcp_config["port"])
    return ""

def check_tcp_node(tcp_node: TcpNode, log_call: Callable[[str], None]):
    log_call("开始检查负载服务节点：{}:{}访问情况".format(tcp_node.host, tcp_node.port))
    if not RequestChecker.check_tcp_node(tcp_node):
        return "无法访问负载服务节点：{}:{}".format(tcp_node.host, tcp_node.port)
    return ""

