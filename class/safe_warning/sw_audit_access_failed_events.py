import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集未成功的未经授权的文件访问尝试'
_version = 1.0
_ps = '检查是否开启未授权文件访问失败日志收集'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_access_failed_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b64 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加：-a always,exit -F arch=b32 -S creat -S open -S openat -S truncate -S ftruncate -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计访问失败事件，越权尝试与探测行为难以追踪；启用access规则后可记录非特权用户因EACCES/EPERM失败的文件访问，提升审计与溯源能力'

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
            return False, '未检测到审计规则文件：/etc/audit/rules.d/audit.rules 或 /etc/audit/audit.rules 缺失'
        body = '\n'.join(contents)
        reqs = [
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EACCES\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b64 ... -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EACCES\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b32 ... -F exit=-EACCES -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EPERM\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b64 ... -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+creat\s+.*-S\s+open\s+.*-S\s+openat\s+.*-S\s+truncate\s+.*-S\s+ftruncate\s+.*-F\s+exit=-EPERM\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+access\s*$', '-a always,exit -F arch=b32 ... -F exit=-EPERM -F auid>=1000 -F auid!=4294967295 -k access')
        ]
        missing = []
        for p, desc in reqs:
            if not re.search(p, body, re.M):
                missing.append(desc)
        if missing:
            return False, '缺少access审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'