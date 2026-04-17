import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保talk客户端未安装'
_version = 1.0
_ps = '检查是否卸载talk客户端'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_talk_client_not_installed.pl")
_tips = [
    "卸载（CentOS/RHEL）：yum remove talk",
    "卸载（Debian/Ubuntu）：apt-get remove talk"
]
_help = ''
_remind = '该软件在使用未加密协议进行通信时存在安全风险，未加密通信易被窃听，建议移除talk客户端'


def check_run():
    try:
        names = ['talk']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, '检测到已安装talk客户端：{}'.format(','.join(found))
        return True, '无风险'
    except:
        return True, '无风险'