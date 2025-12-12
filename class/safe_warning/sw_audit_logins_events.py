import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集登录和注销事件'
_version = 1.0
_ps = '检查是否开启审计登录与失败尝试事件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_logins_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`，添加如下内容"
    "-w /var/log/lastlog -p wa -k logins",
    "-w /var/run/faillock/ -p wa -k logins",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计登录与失败尝试，暴力破解与异常登录难以追踪；启用logins规则后可记录lastlog/faillock变更，提升审计与溯源能力'


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
        reqs = [
            (r'^\s*-w\s+/var/log/lastlog\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/log/lastlog -p wa -k logins'),
            (r'^\s*-w\s+/var/run/faillock/\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/run/faillock/ -p wa -k logins')
        ]
        missing = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, '缺少logins审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'