import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保禁用IPv6'
_version = 1.0
_ps = '检查是否禁用IPv6'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_disabled.pl")
_tips = [
    "编辑`/etc/modprobe.d/disable_ipv6.conf`添加：options ipv6 disable = 1",
]
_help = ''
_remind = '尽管IPv6比IPv4具有许多优势，但很少有组织实现IPv6。如果不使用IPv6，建议禁用IPv6以减少系统的攻击面。\n若要用到IPv6，请忽略此项'


def check_run():
    try:

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
                    return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用IPv6（options ipv6 disable=1）'
    except:
        return True, '无风险'