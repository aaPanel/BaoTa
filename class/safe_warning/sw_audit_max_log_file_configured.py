import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保已配置审核日志存储大小'
_version = 1.0
_ps = '检查是否限制审计日志大小'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_audit_max_log_file_configured.pl")
_tips = [
    "编辑`/etc/audit/auditd.conf`设置：max_log_file = 50（单位MB）",
    "重启审计服务：systemctl restart auditd 或 service auditd restart"
]
_help = ''
_remind = '未限制审计日志大小可能占满磁盘或过小导致频繁滚动而丢失审计数据；合理设置max_log_file可兼顾磁盘占用与取证保留'


def check_run():
    try:
        cfile = '/etc/audit/auditd.conf'
        if not os.path.exists(cfile):
            return False, '未检测到审计配置文件：/etc/audit/auditd.conf 缺失'
        body = public.readFile(cfile) or ''
        m = re.search(r'^\s*max_log_file\s*=\s*(\d+)\s*$', body, re.M)
        if not m:
            return False, 'auditd.conf未配置max_log_file参数'
        val = int(m.group(1))
        if 5 <= val <= 100:
            return True, '无风险'
        return False, 'max_log_file值不在建议范围[5,100]：{}'.format(val)
    except:
        return True, '无风险'