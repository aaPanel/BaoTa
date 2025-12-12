import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保安全的ICMP重定向不被接受'
_version = 1.0
_ps = '检查是否拒绝安全ICMP重定向'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_secure_redirects_not_accept.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv4.conf.all.secure_redirects = 0",
    "net.ipv4.conf.default.secure_redirects = 0",
    "执行：sysctl -w net.ipv4.conf.all.secure_redirects=0",
    "执行：sysctl -w net.ipv4.conf.default.secure_redirects=0",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '安全ICMP重定向与ICMP重定向相同，除非它们来自默认网关列表中列出的网关。 假设这些网关对于您的系统是已知的，并且它们可能是安全的。即使已知的网关仍然可能受到损害。 \n将net.ipv4.conf.all.secure_redirects设置为0可以保护系统免受可能已破坏的已知网关路由表更新的影响。='


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.secure_redirects\s*=\s*0\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.secure_redirects\s*=\s*0\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.secure_redirects')
        if not k2: miss.append('net.ipv4.conf.default.secure_redirects')
        return False, '未禁用安全ICMP重定向：{}'.format(','.join(miss))
    except:
        return True, '无风险'