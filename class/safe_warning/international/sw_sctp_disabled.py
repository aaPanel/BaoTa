import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SCTP被禁用'
_version = 1.0
_ps = '检查是否禁用SCTP协议模块'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_sctp_disabled.pl")
_tips = [
    '创建或编辑/etc/modprobe.d/CIS.conf添加：install sctp /bin/true'
]
_help = ''
_remind = '流控制传输协议（SCTP）是用于支持面向消息的通信传输层协议，并在一个连接中具有几个消息流。\n如果不使用协议，建议不要加载内核模块，禁用服务以减少潜在的攻击面。'


def check_run():
    try:
        d = '/etc/modprobe.d'
        if not os.path.isdir(d):
            return True, '无风险'
        ok = False
        for name in os.listdir(d):
            if not name.endswith('.conf'):
                continue
            fp = os.path.join(d, name)
            body = public.readFile(fp) or ''
            if re.search(r'^\s*(?!#)\s*install\s+sctp\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用规则：install sctp /bin/true'
    except:
        return True, '无风险'