import sys, os

os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保收集内核模块的加载和卸载'
_version = 1.0
_ps = '检查是否开启收集内核模块的加载和卸载'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_modules_events.pl")
_tips = [
    "在`/etc/audit/rules.d/audit.rules`与`/etc/audit/audit.rules`添加："
    "-w /sbin/insmod -p x -k modules",
    "-w /sbin/rmmod -p x -k modules",
    "-w /sbin/modprobe -p x -k modules",
    "-a always,exit -F arch=b64 -S init_module -S delete_module -k modules",
    "重载并重启审计：service auditd restart"
]
_help = ''
_remind = '未审计内核模块加载/卸载，内核级后门与稳定性异常难以追踪；启用modules规则后可记录insmod/rmmod/modprobe及init_module/delete_module系统调用，提升审计与溯源能力'


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
        missing_lines = []
        if not re.search(r'^\s*-w\s+/sbin/insmod\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/insmod -p x -k modules')
        if not re.search(r'^\s*-w\s+/sbin/rmmod\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/rmmod -p x -k modules')
        if not re.search(r'^\s*-w\s+/sbin/modprobe\s+-p\s+x\s+-k\s+modules\s*$', body, re.M):
            missing_lines.append('-w /sbin/modprobe -p x -k modules')
        if not re.search(
                r'^\s*-a\s+always,exit\s+-F\s+arch=b64\s+.*-S\s+init_module\s+.*-S\s+delete_module\s+.*-k\s+modules\s*$',
                body, re.M):
            missing_lines.append('-a always,exit -F arch=b64 -S init_module -S delete_module -k modules')
        if missing_lines:
            return False, '缺少modules审计规则：' + '；'.join(missing_lines)
        return True, '无风险'
    except:
        return True, '无风险'
