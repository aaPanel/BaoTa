import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保ICMP重定向不被接受'
_version = 1.0
_ps = '检查是否拒绝IPv4 ICMP重定向'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_redirects_not_accept.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv4.conf.all.accept_redirects = 0",
    "net.ipv4.conf.default.accept_redirects = 0",
    "执行：sysctl -w net.ipv4.conf.all.accept_redirects=0",
    "执行：sysctl -w net.ipv4.conf.default.accept_redirects=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '攻击者可能会使用伪造的ICMP重定向消息恶意更改系统路由表，并让他们将数据包发送到不正确的网络，并允许捕获系统数据包。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.accept_redirects')
        if not k2: miss.append('net.ipv4.conf.default.accept_redirects')
        return False, '未在/etc/sysctl.conf禁用IPv4 ICMP重定向：{}'.format(','.join(miss))
    except:
        return True, '无风险'