import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保配置了ntp'
_version = 1.0
_ps = '检查是否规范NTP配置'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ntp_configured.pl")
_tips = [
    '编辑`/etc/ntp.conf`：添加以下信息'
    '`restrict -4 default kod nomodify notrap nopeer noquery`',
    '`restrict -6 default kod nomodify notrap nopeer noquery`',
    '启用并重启：`systemctl enable --now ntpd`'
]
_help = ''
_remind = '正确配置ntp可确保时间同步正常工作并提升日志一致性'


def check_run():
    try:
        cfile = '/etc/ntp.conf'
        if not os.path.exists(cfile):
            return True, '无风险'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        miss = []
        if not re.search(r'^\s*(?!#)\s*restrict\s+-4\s+default.*\bnoquery\b', conf, re.M):
            miss.append('缺少restrict -4 default 配置')
        if not re.search(r'^\s*(?!#)\s*restrict\s+-6\s+default.*\bnoquery\b', conf, re.M):
            miss.append('缺少restrict -6 default 配置')
        if not re.findall(r'^\s*(?!#)\s*server\s+\S+', conf, re.M):
            miss.append('缺少server行（/etc/ntp.conf）')
        syscfg = '/etc/sysconfig/ntpd'
        unitf = '/usr/lib/systemd/system/ntpd.service'
        if os.path.exists(syscfg):
            s = public.readFile(syscfg) or ''
            if '-u ntp:ntp' not in s:
                miss.append('ntpd未以ntp用户运行（缺少 -u ntp:ntp）')
        elif os.path.exists(unitf):
            s = public.readFile(unitf) or ''
            if '-u ntp:ntp' not in s:
                miss.append('ntpd未以ntp用户运行（缺少 -u ntp:ntp）')
        if miss:
            return False, 'ntp配置不规范：{}'.format('、'.join(miss))
        return True, '无风险'
    except:
        return True, '无风险'