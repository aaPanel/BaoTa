import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集会话启动信息'
_version = 1.0
_ps = '检查是否开启收集会话启动信息'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_session_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：",
    "-w /var/run/utmp -p wa -k session",
    "-w /var/log/wtmp -p wa -k logins",
    "-w /var/log/btmp -p wa -k logins",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '监视这些文件以进行更改可能会提醒系统管理员在异常时间发生登录，这可能表示入侵者活动'


def check_run():
    try:
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到audit规则文件'
        body = '\n'.join(contents)
        rules = [
            (r'^\s*-w\s+/var/run/utmp\s+-p\s+wa\s+-k\s+session\s*$', '-w /var/run/utmp -p wa -k session'),
            (r'^\s*-w\s+/var/log/wtmp\s+-p\s+wa\s+-k\s+(session|logins)\s*$', '-w /var/log/wtmp -p wa -k logins'),
            (r'^\s*-w\s+/var/log/btmp\s+-p\s+wa\s+-k\s+(session|logins)\s*$', '-w /var/log/btmp -p wa -k logins')
        ]
        missing = []
        for p, line in rules:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, '缺少审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'