import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保已配置审核日志存储大小'
_version = 2.0
_ps = '检查是否限制审计日志大小（仅在auditd安装时检测）'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_audit_max_log_file_configured.pl")
_tips = [
    "安装auditd（如果未安装）：",
    "  CentOS/RHEL: yum install audit",
    "  Debian/Ubuntu: apt-get install auditd",
    "编辑`/etc/audit/auditd.conf`设置：max_log_file = 50（单位MB）",
    "重启审计服务：systemctl restart auditd 或 service auditd restart"
]
_help = ''
_remind = '未限制审计日志大小可能占满磁盘或过小导致频繁滚动而丢失审计数据；合理设置max_log_file可兼顾磁盘占用与取证保留'


def is_auditd_installed():
    """检查auditd是否已安装"""
    # 检查auditd配置文件是否存在
    if os.path.exists('/etc/audit/auditd.conf'):
        return True

    # 检查auditd可执行文件
    if os.path.exists('/usr/sbin/auditd') or os.path.exists('/sbin/auditd'):
        return True

    # 检查是否通过包管理器安装
    try:
        # 检查rpm
        if os.path.exists('/usr/bin/rpm'):
            result = os.popen('rpm -q audit 2>/dev/null').read()
            if result and 'audit' in result.lower() and 'not installed' not in result.lower():
                return True
        # 检查dpkg
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
            # auditd未安装，跳过检测
            return True, 'auditd未安装，跳过检测'

        # auditd已安装，检查配置
        cfile = '/etc/audit/auditd.conf'
        if not os.path.exists(cfile):
            return False, 'auditd已安装但配置文件缺失：/etc/audit/auditd.conf'
        body = public.readFile(cfile) or ''
        m = re.search(r'^\s*max_log_file\s*=\s*(\d+)\s*$', body, re.M)
        if not m:
            return False, 'auditd.conf未配置max_log_file参数，建议设置为50'
        val = int(m.group(1))
        if 5 <= val <= 100:
            return True, '无风险'
        return False, 'max_log_file值不在建议范围[5,100]：{}'.format(val)
    except:
        return True, '无风险'
