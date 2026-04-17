import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保SETroubleshoot未安装'
_version = 1.0
_ps = '是否安装SETroubleshoot'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_setroubleshoot_not_installed.pl")
_tips = [
    "卸载：`yum remove setroubleshoot`",
    "禁用并停止服务：`systemctl disable --now setroubleshoot`"
]
_help = ''
_remind = 'SETroubleshoot服务通过用户友好的界面通知桌面用户SELinux拒绝。 该服务提供有关配置错误，未经授权的入侵和其他潜在错误的重要信息。\nSETroubleshoot服务是在服务器上运行的不必要的守护程序，尤其是在禁用X Windows的情况下。'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'
        paths = [
            '/usr/sbin/setroubleshootd',
            '/usr/bin/sealert',
            '/usr/libexec/setroubleshootd',
            '/usr/lib/systemd/system/setroubleshoot.service'
        ]
        for p in paths:
            if os.path.exists(p):
                return False, '检测到SETroubleshoot组件：{}'.format(p)
        return True, '无风险'
    except:
        return True, '无风险'