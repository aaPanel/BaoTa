import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保ipv6数据包不被源路由接受'
_version = 1.0
_ps = '检查是否拒绝IPv6源路由数据包'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_accept_source_route_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv6.conf.all.accept_source_route = 0",
    "net.ipv6.conf.default.accept_source_route = 0",
    "执行：sysctl -w net.ipv6.conf.all.accept_source_route=0",
    "执行：sysctl -w net.ipv6.conf.default.accept_source_route=0",
    "执行：sysctl -w net.ipv6.route.flush=1",
]
_help = ''
_remind = '防止指定源路由的数据包绕过IPv6网络策略'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.default\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv6.conf.all.accept_source_route')
        if not k2: miss.append('net.ipv6.conf.default.accept_source_route')
        return False, '未在/etc/sysctl.conf禁用IPv6源路由：{}'.format(','.join(miss))
    except:
        return True, '无风险'