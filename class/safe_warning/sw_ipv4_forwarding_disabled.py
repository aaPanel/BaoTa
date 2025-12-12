import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保IP转发禁用(仅限主机)'
_version = 1.0
_ps = '检查是否禁用IPv4转发'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_forwarding_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：net.ipv4.ip_forward = 0",
    "执行：sysctl -w net.ipv4.ip_forward=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '若服务器作为docker宿主机，请忽略此项，将标志设置为0可确保具有多个接口的系统（例如，硬代理）永远无法转发数据包， 因此，不可作为路由器'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.ip_forward\s*=\s*0\s*$', conf, re.M)
        if ok:
            return True, '无风险'
        return False, '未在/etc/sysctl.conf设置：net.ipv4.ip_forward=0'
    except:
        return True, '无风险'