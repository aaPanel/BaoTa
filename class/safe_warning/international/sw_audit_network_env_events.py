import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集修改系统网络环境的事件'
_version = 1.0
_ps = '检查是否开启收集修改系统网络环境的事件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_network_env_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale",
    "-w /etc/issue -p wa -k system-locale",
    "-w /etc/issue.net -p wa -k system-locale",
    "-w /etc/hosts -p wa -k system-locale",
    "-w /etc/sysconfig/network -p wa -k system-locale",
    "-w /etc/sysconfig/network-scripts/ -p wa -k system-locale",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '记录对网络环境文件或系统调用的更改。 以下参数监视sethostname（设置系统主机名）或setdomainname（设置系统域名）系统调用，并在系统调用exit上写入审计事件。 其他参数监视/ etc / issue和/etc/issue.net文件（登录前显示的消息），/ etc / hosts（包含主机名和相关IP地址的文件），/ etc / sysconfig / network文件和/ etc / sysconfig / network-scripts /目录（包含网络接口脚本和配置）。'


def check_run():
    try:
        # 只检测centos系统
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
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+sethostname\s+-S\s+setdomainname\s+-k\s+system-locale\s*$', '-a always,exit -F arch=b64 -S sethostname -S setdomainname -k system-locale'),
            (r'^\s*-w\s+/etc/issue\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/issue -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/issue\.net\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/issue.net -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/hosts\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/hosts -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/sysconfig/network\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/sysconfig/network -p wa -k system-locale'),
            (r'^\s*-w\s+/etc/sysconfig/network-scripts/\s+-p\s+wa\s+-k\s+system-locale\s*$', '-w /etc/sysconfig/network-scripts/ -p wa -k system-locale')
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