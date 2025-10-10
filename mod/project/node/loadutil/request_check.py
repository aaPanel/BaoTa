import requests
import socket

from mod.project.node.dbutil import LoadSite, HttpNode, TcpNode
from mod.project.node.nodeutil import ServerNode


class RequestChecker:

    @staticmethod
    def check_http_node(node: HttpNode, codes=(200,)):
        schema = "https" if node.port in [8443, 443] else "http"
        url = "{}://{}:{}{}".format(schema, node.node_site_name, node.port, node.path)
        try:
            resp = requests.get(url, verify=False, timeout=10)
            if resp.status_code in codes:
                return True
        except:
            pass

        try:
            server_ip = ServerNode.get_node_ip(node.node_id)
            if server_ip:
                url = "{}://{}:{}{}".format(schema, server_ip, node.port, node.path)
                resp = requests.get(url, headers={
                    "Host": node.node_site_name
                }, verify=False, timeout=10)
                if resp.status_code in codes:
                    return True
        except:
            pass
        return False

    @staticmethod
    def check_tcp_node(node: TcpNode) -> bool:
        """使用 socket 测试tcp连接"""
        try:
            # 创建 socket 对象
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                # 设置超时时间
                sock.settimeout(10)
                # 尝试连接
                sock.connect((node.host, node.port))
                return True  # 连接成功
        except (socket.timeout, ConnectionRefusedError, OSError):
            return False  # 连接失败或超时
