import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保数据包不被源路由接受'
_version = 1.0
_ps = '检查是否禁用源路由数据包'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_accept_source_route_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv4.conf.all.accept_source_route = 0",
    "net.ipv4.conf.default.accept_source_route = 0",
    "执行：sysctl -w net.ipv4.conf.all.accept_source_route=0",
    "执行：sysctl -w net.ipv4.conf.default.accept_source_route=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '将net.ipv4.conf.all.accept_source_route和net.ipv4.conf.default.accept_source_route设置为0将禁止系统接受源路由数据包。 假设该系统能够将数据包路由到一个接口上的Internet可路由地址和另一个接口上的私有地址。 假设私有地址不可路由到Internet可路由地址，反之亦然。 在正常路由环境下，来自Internet可路由地址的攻击者无法使用该系统作为到达私有地址系统的方式。 \n但是，如果允许源路由数据包，则可以使用它们来访问专用地址系统，因为可以指定路由，而不是依赖于不允许此路由的路由协议。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.accept_source_route\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.accept_source_route')
        if not k2: miss.append('net.ipv4.conf.default.accept_source_route')
        return False, '未在/etc/sysctl.conf禁用源路由：{}'.format(','.join(miss))
    except:
        return True, '无风险'