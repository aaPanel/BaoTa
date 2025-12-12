import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集对系统管理范围（sudoers）的更改'
_version = 1.0
_ps = '检查是否开启监控sudoers文件与目录变更'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_sudoers_scope_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-w /etc/sudoers -p wa -k scope",
    "-w /etc/sudoers.d/ -p wa -k scope",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '监视系统管理的范围更改。 如果系统已正确配置为强制系统管理员首先以自己身份登录，然后使用sudo命令执行特权命令，则可以监视范围的更改。 当文件或其属性发生更改时，将写入/etc/sudoers文件。 审计记录将使用标识符“范围”进行标记。/etc/sudoers文件中的更改可能表示未对系统管理员活动范围进行未经授权的更改。'


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
        rules = [
            (r'^\s*-w\s+/etc/sudoers\s+-p\s+wa\s+-k\s+scope\s*$', '-w /etc/sudoers -p wa -k scope'),
            (r'^\s*-w\s+/etc/sudoers\.d/\s+-p\s+wa\s+-k\s+scope\s*$', '-w /etc/sudoers.d/ -p wa -k scope')
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