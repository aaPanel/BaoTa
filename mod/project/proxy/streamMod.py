import sys

from mod.project.proxy import tools
from mod.project.proxy.base import StreamRequest
from mod.project.proxy.tcp import TCPProxy
from mod.project.proxy.udp import UDPProxy

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public


def nginx_status():
    """获取Nginx核心运行状态"""
    try:
        import subprocess
        import os

        status = {
            'running': False,
            'master_process': 0,
            'worker_processes': 0,
            'listening_ports': [],
            'connections': {}
        }

        # 检测主进程是否存在
        ps_cmd = "ps -ef | grep 'nginx: master process' | grep -v grep"
        result = subprocess.run(ps_cmd, shell=True, capture_output=True, text=True)
        status['master_process'] = len(result.stdout.strip().split('\n')) if result.stdout else 0
        status['running'] = status['master_process'] > 0

        if status['running']:
            # 获取worker进程数
            worker_cmd = "ps -ef | grep 'nginx: worker process' | grep -v grep | wc -l"
            worker_result = subprocess.run(worker_cmd, shell=True, capture_output=True, text=True)
            status['worker_processes'] = int(worker_result.stdout.strip() or 0)

            # 获取监听端口
            port_cmd = r"ss -tnl | grep nginx | awk '{print $4}' | awk -F: '{print $NF}' | sort -u"
            port_result = subprocess.run(port_cmd, shell=True, capture_output=True, text=True)
            status['listening_ports'] = list(set(port_result.stdout.strip().split('\n')))

            # 获取连接状态统计
            conn_cmd = "ss -ant | grep -i est | awk '{print $1}' | sort | uniq -c"
            conn_result = subprocess.run(conn_cmd, shell=True, capture_output=True, text=True)
            for line in conn_result.stdout.strip().split('\n'):
                if line:
                    count, state = line.strip().split()
                    status['connections'][state.upper()] = int(count)

        # 获取配置文件状态
        test_cmd = "nginx -t 2>&1 | grep successful"
        test_result = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        status['config_valid'] = 'successful' in test_result.stdout

        return True, status

    except Exception as e:
        return False, "状态获取失败: {}".format(str(e))


class main(TCPProxy, UDPProxy):
    def __init__(self):
        self.request = StreamRequest()
        self.tcp_proxy = TCPProxy()
        self.udp_proxy = UDPProxy()
        super().__init__()

    def dispatch(self, handle_name):
        """

        Args:
            handle_name:

        Returns:

        """
        tcp_handle = getattr(self.tcp_proxy, handle_name)
        udp_handle = getattr(self.udp_proxy, handle_name)

        if not (hasattr(self.tcp_proxy, handle_name) or hasattr(self.tcp_proxy, handle_name)):
            raise ValueError("Not Support {}".format(handle_name))
        elif handle_name == 'list':
            return tcp_handle(self.request)

        if self.request.protocol == 'tcp':
            return tcp_handle(self.request)
        elif self.request.protocol == 'udp':
            return udp_handle(self.request)
        elif self.request.protocol == 'tcp/udp':
            _tcp_request = tools.update_attr(StreamRequest(), self.request)
            _udp_request = tools.update_attr(StreamRequest(), self.request)
            _tcp_request.protocol = 'tcp'
            _udp_request.protocol = 'udp'
            return {'tcp': tcp_handle(_tcp_request), 'udp': udp_handle(_udp_request)}
        raise ValueError("'request.protocol' Not Found")

    def get(self, get):
        wc_err = public.checkWebConfig()
        if not wc_err:
            return public.returnResult(
                status=False,
                msg='ERROR: 检测到配置文件有错误,请先排除后再操作<br><br><a style="color:red;">' +
                    wc_err.replace("\n", '<br>') + '</a>'
            )

        status, data = nginx_status()
        if not status:
            return public.returnResult(status=False, msg=data)
        elif not data.get('running'):
            return public.returnResult(status=False, msg='Nginx未运行')

        # public.print_log(get.__dict__)
        try:
            get['listen'] = get.get('listen_port')  # 与前端参数匹配
            self.request = tools.update_attr(self.request, get)
            response = self.dispatch(self.request.handle)
            public.print_log(type(response), response)
            if isinstance(response, str):
                return public.returnResult(True, msg=response)
            return public.returnResult(True, data=response)
        except Exception as e:
            return public.returnResult(False, msg="错误:" + str(e))
