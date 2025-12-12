import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保LDAP客户端未安装'
_version = 1.0
_ps = '检查是否卸载LDAP客户端'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ldap_client_not_installed.pl")
_tips = [
    "卸载（CentOS/RHEL）：yum remove openldap-clients",
    "卸载（Debian/Ubuntu）：apt-get remove ldap-utils"
]
_help = ''
_remind = '如果系统不需要充当LDAP客户端，建议删除软件以减少潜在的攻击面。'


def check_run():
    try:
        names = ['ldapsearch', 'ldapmodify', 'ldapadd']
        dirs = ['/usr/bin', '/bin', '/usr/sbin', '/sbin']
        found = []
        for d in dirs:
            for n in names:
                p = os.path.join(d, n)
                if os.path.exists(p):
                    found.append(p)
        if found:
            return False, '检测到已安装LDAP客户端工具：{}'.format(','.join(found))
        return True, '无风险'
    except:
        return True, '无风险'