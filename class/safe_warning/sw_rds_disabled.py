import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保RDS被禁用'
_version = 1.0
_ps = '检查是否禁用RDS内核模块'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_rds_disabled.pl")
_tips = [
    '创建或编辑`/etc/modprobe.d/CIS.conf`添加：`install rds /bin/true`'
]
_help = ''
_remind = '可靠数据报套接字（RDS）协议是一种传输层协议，在群集节点之间提供低延迟，高带宽的通信。\n如果不使用协议，建议不要加载内核模块，禁用服务以减少潜在的攻击面。'


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
            if re.search(r'^\s*(?!#)\s*install\s+rds\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用规则：install rds /bin/true'
    except:
        return True, '无风险'