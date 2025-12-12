import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保已安装SELinux或AppArmor'
_version = 1.0
_ps = '检查是否安装SELinux或AppArmor'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mac_system_installed.pl")
_tips = [
    "安装SELinux（CentOS/RHEL）：yum install selinux-policy-targeted policycoreutils",
    "安装SELinux（Debian/Ubuntu）：apt-get install selinux",
    "安装AppArmor（Debian/Ubuntu）：apt-get install apparmor apparmor-utils"
]
_help = ''
_remind = 'SELinux和AppArmor提供强制访问控制。如果没有安装强制访问控制系统，则只能使用默认的自由访问控制系统。'


def check_run():
    try:
        selinux_paths = [
            '/etc/selinux',
            '/usr/sbin/selinuxenabled',
            '/usr/sbin/sestatus',
            '/usr/bin/getenforce'
        ]
        apparmor_paths = [
            '/etc/apparmor',
            '/etc/apparmor.d',
            '/sbin/apparmor_status',
            '/usr/sbin/aa-status'
        ]
        has_sel = any(os.path.exists(p) for p in selinux_paths)
        has_app = any(os.path.exists(p) for p in apparmor_paths)
        if has_sel or has_app:
            return True, '无风险'
        missing = []
        for p in selinux_paths + apparmor_paths:
            if not os.path.exists(p):
                missing.append(p)
        return False, '未安装强制访问控制（缺失组件路径：{}）'.format('、'.join(missing[:6]))
    except:
        return True, '无风险'