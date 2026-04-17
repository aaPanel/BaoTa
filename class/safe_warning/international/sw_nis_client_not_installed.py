import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保NIS客户端未安装'
_version = 1.0
_ps = '检查是否卸载NIS客户端'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_nis_client_not_installed.pl")
_tips = [
    "卸载（CentOS/RHEL）：yum remove ypbind",
    "卸载（Debian/Ubuntu）：apt-get remove nis"
]
_help = ''
_remind = 'NIS服务本质上是一个不安全的系统，易受DoS攻击、缓冲区溢出以及查询NIS映射的身份验证不佳。NIS通常已被轻量级目录访问协议（LDAP）等协议所取代。\n建议删除此服务。'


def check_run():
    try:
        names = ['ypbind']
        dirs = ['/usr/sbin', '/sbin', '/usr/bin', '/bin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, '检测到已安装NIS客户端组件：{}'.format(','.join(found))
        return True, '无风险'
    except:
        return True, '无风险'