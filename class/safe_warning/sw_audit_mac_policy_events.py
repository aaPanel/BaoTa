import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集修改系统强制访问控制的事件'
_version = 1.0
_ps = '检查是否收集修改系统强制访问控制的事件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_mac_policy_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-w /etc/selinux/ -p wa -k MAC-policy",
    "若使用了apparmor的系统中，还需添加：",
    "-w /etc/apparmor/ -p wa -k MAC-policy",
    "-w /etc/apparmor.d/ -p wa -k MAC-policy",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计强制访问控制策略变更，策略被篡改与安全上下文异常难以追踪；启用MAC-policy规则后可记录SELinux/AppArmor策略写入与属性变更，提升审计与溯源能力'


def check_run():
    try:
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到审计规则文件：/etc/audit/rules.d/audit.rules 或 /etc/audit/audit.rules 缺失'
        body = '\n'.join(contents)
        need_sel = os.path.isdir('/etc/selinux')
        need_app = os.path.isdir('/etc/apparmor') or os.path.isdir('/etc/apparmor.d')
        missing_lines = []
        if need_sel and not re.search(r'^\s*-w\s+/etc/selinux/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M):
            missing_lines.append('SELinux：-w /etc/selinux/ -p wa -k MAC-policy')
        if need_app:
            ok1 = re.search(r'^\s*-w\s+/etc/apparmor/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M)
            ok2 = re.search(r'^\s*-w\s+/etc/apparmor\.d/\s+-p\s+wa\s+-k\s+MAC-policy\s*$', body, re.M)
            if not ok1:
                missing_lines.append('AppArmor：-w /etc/apparmor/ -p wa -k MAC-policy')
            if not ok2:
                missing_lines.append('AppArmor：-w /etc/apparmor.d/ -p wa -k MAC-policy')
        if missing_lines:
            return False, '缺少MAC-policy审计规则：' + '；'.join(missing_lines)
        return True, '无风险'
    except:
        return True, '无风险'