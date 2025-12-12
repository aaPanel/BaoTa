import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保可疑数据包被记录'
_version = 1.0
_ps = '启用可疑数据包日志（log_martians）'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ipv4_log_martians_enabled.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：",
    "net.ipv4.conf.all.log_martians = 1",
    "net.ipv4.conf.default.log_martians = 1",
    "执行：sysctl -w net.ipv4.conf.all.log_martians=1",
    "执行：sysctl -w net.ipv4.conf.default.log_martians=1",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '记录不可路由来源数据包，提升可见性与溯源能力'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        k1 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.all\.log_martians\s*=\s*1\s*$', conf, re.M)
        k2 = re.search(r'^\s*(?!#)\s*net\.ipv4\.conf\.default\.log_martians\s*=\s*1\s*$', conf, re.M)
        if k1 and k2:
            return True, '无风险'
        miss = []
        if not k1: miss.append('net.ipv4.conf.all.log_martians')
        if not k2: miss.append('net.ipv4.conf.default.log_martians')
        return False, '未启用可疑数据包日志：{}'.format(','.join(miss))
    except:
        return True, '无风险'