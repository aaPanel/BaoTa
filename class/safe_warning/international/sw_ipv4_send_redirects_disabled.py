import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保数据包重定向发送功能已禁用（仅限主机）'
_version = 1.0
_ps = '检查是否禁用IPv4发送重定向'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_send_redirects_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv4.conf.all.send_redirects = 0",
    "net.ipv4.conf.default.send_redirects = 0",
    "执行：sysctl -w net.ipv4.conf.all.send_redirects=0",
    "执行：sysctl -w net.ipv4.conf.default.send_redirects=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = 'ICMP重定向用于将路由信息发送到其他主机。 由于主机本身不充当路由器（在仅主机配置中），因此无需发送重定向，若服务器作为docker宿主机，请忽略此项。\n攻击者可以使用受感染的主机将无效的ICMP重定向发送到其他路由器设备，以试图破坏路由并使用户访问由攻击者设置的无效系统。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.send_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.send_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.send_redirects')
        if not k2: miss.append('net.ipv4.conf.default.send_redirects')
        return False, '未在/etc/sysctl.conf禁用IPv4重定向发送：{}'.format(','.join(miss))
    except:
        return True, '无风险'