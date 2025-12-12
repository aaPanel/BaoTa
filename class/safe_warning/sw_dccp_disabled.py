import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保DCCP已被禁用'
_version = 1.0
_ps = '检查是否禁用DCCP内核模块'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_dccp_disabled.pl")
_tips = [
    '创建或编辑`/etc/modprobe.d/CIS.conf`添加：`install dccp /bin/true`',
    '可选：`echo blacklist dccp >> /etc/modprobe.d/CIS.conf`',
    '卸载已加载模块：`modprobe -r dccp`'
]
_help = ''
_remind = '数据报拥塞控制协议（DCCP）是支持流媒体和电话的传输层协议。如果不需要协议，建议不要安装驱动程序以减少潜在的攻击面。'


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
            if re.search(r'^\s*(?!#)\s*install\s+dccp\s+/bin/true\s*$', body, re.M):
                ok = True
                break
        if ok:
            return True, '无风险'
        return False, '未在/etc/modprobe.d/*.conf配置禁用规则：install dccp /bin/true'
    except:
        return True, '无风险'