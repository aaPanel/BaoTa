import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保广播ICMP请求被忽略'
_version = 1.0
_ps = '检查广播ICMP请求是否忽略'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_icmp_echo_ignore_broadcasts.pl")
_tips = [
    "在`/etc/sysctl.conf`设置：net.ipv4.icmp_echo_ignore_broadcasts = 1",
    "执行：sysctl -w net.ipv4.icmp_echo_ignore_broadcasts=1",
    "执行：sysctl -w net.ipv4.route.flush=1",
]
_help = ''
_remind = '将net.ipv4.icmp_echo_ignore_broadcasts设置为1将导致系统忽略对广播和多播地址的所有ICMP回送和时间戳请求。接受带有网络广播或多播目的地的ICMP回送和时间戳请求可用于欺骗主机启动（ 或参与蓝精灵的袭击。 Smurf攻击依赖于攻击者使用欺骗性源地址发送大量ICMP广播消息。 接收此消息并响应的所有主机都会将echo-reply消息发送回欺骗地址，该地址可能不可路由。 \n如果许多主机响应数据包，则网络上的流量可能会显着增加。'


def check_run():
    try:
        conf = public.readFile('/etc/sysctl.conf') or ''
        ok = re.search(r'^\s*(?!#)\s*net\.ipv4\.icmp_echo_ignore_broadcasts\s*=\s*1\s*$', conf, re.M)
        if ok:
            return True, '无风险'
        return False, '未配置sysctl：net.ipv4.icmp_echo_ignore_broadcasts=1'
    except:
        return True, '无风险'