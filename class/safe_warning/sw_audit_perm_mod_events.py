import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集自主访问控制权限修改事件'
_version = 1.0
_ps = '检查是否开启收集自主访问控制权限修改事件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_perm_mod_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "-a always,exit -F arch=b32 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '发现权限与属性的异常调整，辅助策略违规定位'


def check_run():
    try:
        # 只检查centos系统
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
        req = [
            r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+chmod\s+.*-S\s+fchmod\s+.*-S\s+fchmodat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$',
            r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+chmod\s+.*-S\s+fchmod\s+.*-S\s+fchmodat\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$',
            r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+chown\s+.*-S\s+fchown\s+.*-S\s+fchownat\s+.*-S\s+lchown\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$',
            r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+chown\s+.*-S\s+fchown\s+.*-S\s+fchownat\s+.*-S\s+lchown\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$',
            r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+setxattr\s+.*-S\s+lsetxattr\s+.*-S\s+fsetxattr\s+.*-S\s+removexattr\s+.*-S\s+lremovexattr\s+.*-S\s+fremovexattr\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$',
            r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+.*-S\s+setxattr\s+.*-S\s+lsetxattr\s+.*-S\s+fsetxattr\s+.*-S\s+removexattr\s+.*-S\s+lremovexattr\s+.*-S\s+fremovexattr\s+.*-F\s+auid>=1000\s+.*-F\s+auid!=4294967295\s+.*-k\s+perm_mod\s*$'
        ]
        for p in req:
            if not re.search(p, body, re.M):
                return False, '缺少perm_mod审计规则'
        return True, '无风险'
    except:
        return True, '无风险'
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
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+chmod\s+-S\s+fchmod\s+-S\s+fchmodat\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b64 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+chmod\s+-S\s+fchmod\s+-S\s+fchmodat\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b32 -S chmod -S fchmod -S fchmodat -F auid>=1000 -F auid!=4294967295 -k perm_mod'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+chown\s+-S\s+fchown\s+-S\s+fchownat\s+-S\s+lchown\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b64 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+chown\s+-S\s+fchown\s+-S\s+fchownat\s+-S\s+lchown\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b32 -S chown -S fchown -S fchownat -S lchown -F auid>=1000 -F auid!=4294967295 -k perm_mod'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+setxattr\s+-S\s+lsetxattr\s+-S\s+fsetxattr\s+-S\s+removexattr\s+-S\s+lremovexattr\s+-S\s+fremovexattr\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b64 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+setxattr\s+-S\s+lsetxattr\s+-S\s+fsetxattr\s+-S\s+removexattr\s+-S\s+lremovexattr\s+-S\s+fremovexattr\s+-F\s+auid>=1000\s+-F\s+auid!=4294967295\s+-k\s+perm_mod\s*$', '-a always,exit -F arch=b32 -S setxattr -S lsetxattr -S fsetxattr -S removexattr -S lremovexattr -S fremovexattr -F auid>=1000 -F auid!=4294967295 -k perm_mod')
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