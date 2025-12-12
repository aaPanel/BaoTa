import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保TCP Wrappers已安装'
_version = 1.0
_ps = '检查是否安装TCP Wrappers'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_tcp_wrappers_installed.pl")
_tips = [
    'centos系统执行安装命令：yum install tcp_wrappers '
    'Unbuntu/debian系统：执行 apt-get install tcpd'
]
_help = ''
_remind = 'TCP Wrappers为能够支持它的服务提供简单的访问列表和标准化日志记录方法。\n建议所有支持TCPWrappers的服务都使用它。'


def check_run():
    try:
        paths = [
            '/usr/sbin/tcpd',
            '/lib64/libwrap.so',
            '/lib/libwrap.so',
            '/usr/lib/libwrap.so',
            '/usr/lib64/libwrap.so'
        ]
        for p in paths:
            try:
                if os.path.exists(p):
                    return True, '无风险'
            except:
                pass
        return False, '未安装TCP Wrappers'
    except:
        return True, '无风险'