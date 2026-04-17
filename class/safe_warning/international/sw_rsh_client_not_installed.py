import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保rsh客户端未安装'
_version = 1.0
_ps = '检查是否卸载rsh/rcp/rlogin客户端'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_rsh_client_not_installed.pl")
_tips = [
    "卸载（Debian/Ubuntu）：apt-get remove rsh-client rsh-redone-client",
    "检查是否有遗留软链：ls -l /usr/bin/rsh /usr/bin/rcp /usr/bin/rlogin",
    "若存在软链，建议删除：rm /usr/bin/rsh /usr/bin/rcp /usr/bin/rlogin"
]
_help = ''
_remind = '这些遗留客户机包含许多安全风险，并已被更安全的ssh包所取代。即使服务器被删除，最好确保客户端也被删除，以防止用户无意中尝试使用这些命令，从而暴露其凭据。\n注意，删除rsh包会删除rsh、rcp和rlogin的客户机。'


def check_run():
    try:
        names = ['rsh', 'rcp', 'rlogin']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, '检测到已安装rsh系列客户端：{}'.format(','.join(found))
        return True, '无风险'
    except:
        return True, '无风险'