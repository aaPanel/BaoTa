import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = 'IPv6安全配置检测'
_version = 2.0
_ps = '检查IPv6配置是否安全（不禁用，但确保安全设置）'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ipv6_disabled.pl")
_tips = [
    "如果不需要使用IPv6，可在`/etc/modprobe.d/disable_ipv6.conf`添加：options ipv6 disable=1",
    "如果使用IPv6，建议配置以下安全参数：",
    "  net.ipv6.conf.all.accept_ra=0 (禁用路由器通告)",
    "  net.ipv6.conf.all.accept_redirects=0 (禁用重定向)",
]
_help = ''
_remind = 'IPv6是现代网络协议，不建议强制禁用。如果使用IPv6，应确保配置安全参数以减少攻击面。'


def check_run():
    """
    检测IPv6配置安全性
    1. 如果IPv6已禁用 -> 无风险
    2. 如果IPv6启用但配置了安全参数 -> 无风险
    3. 如果IPv6启用且未配置安全参数 -> 提示风险
    """
    try:
        # 检查IPv6是否被禁用
        dirs = ['/etc/modprobe.d']
        pat = re.compile(r'^\s*(?!#)\s*options\s+ipv6\s+disable\s*=\s*1\s*$', re.M)
        ipv6_disabled = False
        for d in dirs:
            if not os.path.isdir(d):
                continue
            for name in os.listdir(d):
                if not name.endswith('.conf'):
                    continue
                fp = os.path.join(d, name)
                body = public.readFile(fp) or ''
                if pat.search(body):
                    ipv6_disabled = True
                    break
            if ipv6_disabled:
                break

        # 如果IPv6已禁用，无风险
        if ipv6_disabled:
            return True, 'IPv6已禁用，无风险'

        # IPv6未禁用，检查是否配置了安全参数
        conf = public.readFile('/etc/sysctl.conf') or ''

        # 检查关键IPv6安全参数
        accept_ra = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_ra\s*=\s*0\s*$', conf, re.M)
        accept_redirects = re.search(r'^\s*(?!#)\s*net\.ipv6\.conf\.all\.accept_redirects\s*=\s*0\s*$', conf, re.M)

        # 如果配置了安全参数，无风险
        if accept_ra and accept_redirects:
            return True, 'IPv6已启用且配置了安全参数，无风险'

        # IPv6启用但未配置安全参数，提示建议
        miss = []
        if not accept_ra:
            miss.append('net.ipv6.conf.all.accept_ra=0')
        if not accept_redirects:
            miss.append('net.ipv6.conf.all.accept_redirects=0')

        return False, 'IPv6已启用但未配置安全参数，建议设置：{}'.format(', '.join(miss))
    except:
        return True, '无风险'
