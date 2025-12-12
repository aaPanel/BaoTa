import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保telnet客户端未安装'
_version = 1.0
_ps = '检查是否卸载telnet客户端'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_telnet_client_not_installed.pl")
_tips = [
    "卸载（CentOS/RHEL）：yum remove telnet",
    "卸载（Debian/Ubuntu）：apt-get remove telnet"
]
_help = ''
_remind = 'telnet协议不安全且未加密。使用未加密的传输媒介可能导致未经授权的用户窃取凭证。\nssh包提供加密会话和更强的安全性，并且包含在大多数Linux发行版中。'


def check_run():
    try:
        names = ['telnet']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, '检测到已安装telnet客户端：{}'.format(','.join(found))
        return True, '无风险'
    except:
        return True, '无风险'