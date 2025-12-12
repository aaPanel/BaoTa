import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集系统管理员操作'
_version = 1.0
_ps = '检查是否开启收集系统管理员操作'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_sudo_log_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-w /var/log/sudo.log -p wa -k actions",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '将管理员命令与审计记录关联，发现未授权操作与篡改'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到audit规则文件'
        body = '\n'.join(contents)
        ok = re.search(r'^\s*-w\s+/var/log/sudo\.log\s+-p\s+wa\s+-k\s+actions\s*$', body, re.M)
        if ok:
            return True, '无风险'
        return False, 'auditd日志收集缺少审计规则：-w /var/log/sudo.log -p wa -k actions'
    except:
        return True, '无风险'