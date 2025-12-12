import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保不接受IPv6重定向'
_version = 1.0
_ps = '检查是否拒绝IPv6重定向'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_redirects_not_accept.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv6.conf.all.accept_redirects = 0",
    "net.ipv6.conf.default.accept_redirects = 0",
    "执行：sysctl -w net.ipv6.conf.all.accept_redirects=0",
    "执行：sysctl -w net.ipv6.conf.default.accept_redirects=0",
    "执行：sysctl -w net.ipv6.route.flush=1",
]
_help = ''
_remind = '此设置可防止系统接受ICMP重定向。 ICMP重定向告诉系统有关发送流量的备用路由。建议系统不接受ICMP重定向，因为它们可能被欺骗将流量路由到受感染的计算机。 \n在系统内设置硬路由（通常是到可信路由器的单个默认路由）可以保护系统免受错误路由的影响。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.default\.accept_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv6.conf.all.accept_redirects')
        if not k2: miss.append('net.ipv6.conf.default.accept_redirects')
        return False, '未在/etc/sysctl.conf禁用IPv6重定向：{}'.format(','.join(miss))
    except:
        return True, '无风险'