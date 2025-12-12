import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集修改日期和时间信息的事件'
_version = 1.0
_ps = '检查是否开启监控时间相关系统调用'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_time_change_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`和`/etc/audit/audit.rules`添加：",
    "-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change",
    "-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change",
    "-a always,exit -F arch=b64 -S clock_settime -k time-change",
    "-a always,exit -F arch=b32 -S clock_settime -k time-change",
    "-w /etc/localtime -p wa -k time-change",
    "重启：`service auditd restart`"
]
_help = ''
_remind = '捕获已修改系统日期和/或时间的事件。 设置此部分中的参数以确定adjtimex（调整内核时钟），settimeofday（设置时间，使用时间和时区结构）是否为stime（使用自1970年1月1日以来的秒数）或clock_settime（允许设置多个内部时间） 时钟和计时器）系统调用已执行，并在退出时始终将审计记录写入/var/log/audit.log文件，使用标识符“time-change”标记记录，系统日期和/或时间的意外更改可能是系统上恶意活动的迹象。'


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
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+adjtimex\s+-S\s+settimeofday\s+-k\s+time-change\s*$', '-a always,exit -F arch=b64 -S adjtimex -S settimeofday -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+adjtimex\s+-S\s+settimeofday\s+-S\s+stime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b32 -S adjtimex -S settimeofday -S stime -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+-S\s+clock_settime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b64 -S clock_settime -k time-change'),
            (r'^\s*-a\s+always,exit\s+-F\s+arch=b32\s+-S\s+clock_settime\s+-k\s+time-change\s*$', '-a always,exit -F arch=b32 -S clock_settime -k time-change'),
            (r'^\s*-w\s+/etc/localtime\s+-p\s+wa\s+-k\s+time-change\s*$', '-w /etc/localtime -p wa -k time-change')
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