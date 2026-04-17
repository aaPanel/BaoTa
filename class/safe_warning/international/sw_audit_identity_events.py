import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集修改用户/组信息的事件'
_version = 2.0
_ps = '检查是否开启监控账户与口令文件变更事件（仅在auditd安装时检测）'
_level = 1
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_identity_events.pl")
_tips = [
    "安装auditd（如果未安装）：",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加如下信息",
    "-w /etc/group -p wa -k identity",
    "-w /etc/passwd -p wa -k identity",
    "-w /etc/gshadow -p wa -k identity",
    "-w /etc/shadow -p wa -k identity",
    "-w /etc/security/opasswd -p wa -k identity",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '若未审计账户与口令文件的写入/属性变更，账户被篡改将难以追溯；启用identity规则后可记录并检索异常改动，提升入侵发现与追踪能力'


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
            (r'^\s*-w\s+/etc/group\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/group -p wa -k identity'),
            (r'^\s*-w\s+/etc/passwd\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/passwd -p wa -k identity'),
            (r'^\s*-w\s+/etc/gshadow\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/gshadow -p wa -k identity'),
            (r'^\s*-w\s+/etc/shadow\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/shadow -p wa -k identity'),
            (r'^\s*-w\s+/etc/security/opasswd\s+-p\s+wa\s+-k\s+identity\s*$', '-w /etc/security/opasswd -p wa -k identity')
        ]
        miss_lines = []
        for p, line in reqs:
            if not re.search(p, body, re.M):
                miss_lines.append(line)
        if miss_lines:
            return False, '缺少identity审计规则：' + '；'.join(miss_lines)
        return True, '无风险'
    except:
        return False, '监控账户与口令文件变更检测异常'
