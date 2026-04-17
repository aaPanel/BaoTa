import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集用户的文件删除事件'
_version = 1.0
_ps = '检查是否开启收集用户的文件删除事件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_delete_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计删除/重命名事件，受保护文件被非特权用户删除或篡改将难以追踪；启用delete规则后可记录关键文件的删除/重命名行为，提升溯源与合规能力'


def check_run():
    try:
        # 仅限centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到审计规则文件：/etc/audit/rules.d/audit.rules 或 /etc/audit/audit.rules 缺失'
        body = '\n'.join(contents)
        reqs = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+unlink\s+.*-S\s+unlinkat\s+.*-S\s+rename\s+.*-S\s+renameat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+delete\s*$', '-a always,exit -F arch=b64 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+unlink\s+.*-S\s+unlinkat\s+.*-S\s+rename\s+.*-S\s+renameat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+delete\s*$', '-a always,exit -F arch=b32 -S unlink -S unlinkat -S rename -S renameat -F auid>=1000 -F auid!=4294967295 -k delete')
        ]
        missing = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, '缺少delete审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'