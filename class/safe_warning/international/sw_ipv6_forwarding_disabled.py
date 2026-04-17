import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保IPv6转发禁用（仅限主机）'
_version = 1.0
_ps = '检查是否禁用IPv6转发（主机）'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_forwarding_disabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：net.ipv6.conf.all.forwarding = 0",
    "执行：sysctl -w net.ipv6.conf.all.forwarding=0",
    "执行：sysctl -w net.ipv6.route.flush=1",
]
_help = ''
_remind = 'net.ipv6.conf.all.forwarding标志用于告诉系统是否可以转发数据包。\n将标志设置为0可确保具有多个接口的系统（例如，硬代理）永远无法转发数据包， 因此，不可作为路由器，\n若服务器作为docker宿主机，此项不能加固。'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.forwarding\s*=\s*0\s*$', conf, re.M)
        if ok:
            return True, '无风险'
        return False, '未配置sysctl：net.ipv6.conf.all.forwarding=0'
    except:
        return True, '无风险'