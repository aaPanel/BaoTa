import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保伪造的ICMP响应被忽略'
_version = 1.0
_ps = '检查是否忽略伪造ICMP错误响应'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_icmp_ignore_bogus.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：net.ipv4.icmp_ignore_bogus_error_responses = 1",
    "执行：sysctl -w net.ipv4.icmp_ignore_bogus_error_responses=1",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '将icmp_ignore_bogus_error_responses设置为1可防止内核从广播重构中记录虚假响应（RFC-1122不兼容），从而防止文件系统填满无用的日志消息。\n某些路由器（以及一些攻击者）将发送违反RFC-1122和 尝试用许多无用的错误消息填充日志文件系统。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.icmp_ignore_bogus_error_responses\s*=\s*1\s*$', conf, re.M)
        if ok:
            return True, '无风险'
        return False, '未配置sysctl：net.ipv4.icmp_ignore_bogus_error_responses=1'
    except:
        return True, '无风险'