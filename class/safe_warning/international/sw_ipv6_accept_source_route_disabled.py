import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保ipv6数据包不被源路由接受'
_version = 2.0
_ps = '检查是否拒绝IPv6源路由数据包（仅在IPv6启用时检测）'
_level = 2
_date = '2025-01-15'
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


def is_ipv6_enabled():
    """检查IPv6是否启用"""
    # 检查是否禁用了IPv6模块
    dirs = ['/etc/modprobe.d']
    pat = re.compile(r'^\s*(?!#)\s*options\s+ipv6\s+disable\s*=\s*1\s*$', re.M)
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if pat.search(body):
                return False  # IPv6被禁用

    # 检查是否有IPv6地址
    try:
        if os.path.exists('/proc/net/if_inet6'):
            content = public.readFile('/proc/net/if_inet6')
            if content and content.strip():
                return True  # 有IPv6地址，说明IPv6启用
    except:
        pass

    return False  # 默认认为IPv6未启用


def check_run():
    try:
        # 如果IPv6未启用，跳过检测
        if not is_ipv6_enabled():
            return True, 'IPv6未启用，跳过检测'

        # IPv6启用，检查是否禁用了源路由
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
