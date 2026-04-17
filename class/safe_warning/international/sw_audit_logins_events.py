import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集登录和注销事件'
_version = 2.0
_ps = '检查是否开启审计登录与失败尝试事件（仅在auditd安装时检测）'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_logins_events.pl")
_tips = [
    "安装auditd（如果未安装）：",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`，添加如下内容",
    "-w /var/log/lastlog -p wa -k logins",
    "-w /var/run/faillock/ -p wa -k logins",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计登录与失败尝试，暴力破解与异常登录难以追踪；启用logins规则后可记录lastlog/faillock变更，提升审计与溯源能力'


def is_auditd_installed():
    """检查auditd是否已安装"""
    if os.path.exists('/usr/sbin/auditd') or os.path.exists('/sbin/auditd'):
        return True
    try:
        if os.path.exists('/usr/bin/rpm'):
            result = os.popen('rpm -q audit 2>/dev/null').read()
            if result and 'audit' in result.lower() and 'not installed' not in result.lower():
                return True
        elif os.path.exists('/usr/bin/dpkg'):
            result = os.popen('dpkg -l auditd 2>/dev/null').read()
            if result and 'auditd' in result.lower() and 'no packages found' not in result.lower():
                return True
    except:
        pass
    return False


def check_run():
    try:
        # 首先检查auditd是否安装
        if not is_auditd_installed():
            return True, 'auditd未安装，跳过检测'

        # auditd已安装，检查审计规则
        files = ['/etc/audit/rules.d/audit.rules', '/etc/audit/audit.rules']
        contents = []
        for f in files:
            if os.path.exists(f):
                contents.append(public.readFile(f) or '')
        if not contents:
            return False, '未检测到审计规则文件：/etc/audit/rules.d/audit.rules 或 /etc/audit/audit.rules 缺失'
        body = '\n'.join(contents)
        reqs = [
            (r'^\s*-w\s+/var/log/lastlog\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/log/lastlog -p wa -k logins')
        ]
        # 仅当faillock目录存在时才检测其规则（与修复方案保持一致）
        if os.path.exists('/var/run/faillock/'):
            reqs.append(
                (r'^\s*-w\s+/var/run/faillock/\s+-p\s+wa\s+-k\s+logins\s*$', '-w /var/run/faillock/ -p wa -k logins')
            )
        missing = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                missing.append(line)
        if missing:
            return False, '缺少logins审计规则：' + '；'.join(missing)
        return True, '无风险'
    except:
        return True, '无风险'
