import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保SELinux安装'
_version = 1.0
_ps = '检查是否安装SELinux组件'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_selinux_installed.pl")
_tips = [
    "安装SELinux基础组件：`yum install libselinux`"
]
_help = ''
_remind = '安装SELinux为系统提供更强的访问控制与隔离能力'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        paths = [
            '/usr/sbin/selinuxenabled',
            '/usr/sbin/sestatus',
            '/usr/bin/getenforce',
            '/usr/lib64/libselinux.so',
            '/usr/lib/libselinux.so'
        ]
        for p in paths:
            if os.path.exists(p):
                return True, '无风险'
        return False, '未检测到SELinux命令或库（selinuxenabled/sestatus/getenforce 或 libselinux.so）'
    except:
        return True, '无风险'