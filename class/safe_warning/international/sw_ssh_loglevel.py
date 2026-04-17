import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SSH LogLevel设置为INFO'
_version = 1.0
_ps = '检查是否设置SSH日志级别为INFO/VERBOSE'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_loglevel.pl")
_tips = [
    "编辑/etc/ssh/sshd_config文件，如下设置参数：",
    "LogLevel VERBOSE 或 LogLevel INFO",
    "重启 sshd : systemctl restart sshd",
]
_help = ''
_remind = '确保SSH LogLevel设置为INFO,记录登录和注销活动，提升审计与溯源'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*LogLevel\s+(\S+)', conf, re.M)
        if not matches:
            return True, '无风险'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v not in ('info', 'verbose'):
            return False, 'LogLevel未设置为INFO或VERBOSE'
        return True, '无风险'
    except:
        return True, '无风险'