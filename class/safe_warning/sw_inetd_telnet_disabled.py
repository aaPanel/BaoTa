import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保telnet服务未启用'
_version = 1.0
_ps = '检查是否禁用telnet服务'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_telnet_disabled.pl")
_tips = [
    "在`/etc/inetd.conf`与`/etc/inetd.d/*`注释/删除以`telnet`开头的行",
    "在`/etc/xinetd.conf`与`/etc/xinetd.d/*`将`telnet`服务`disable = yes`"
]
_help = ''
_remind = 'elnet-server软件包包含telnet守护进程，它通过telnet协议接受来自其他系统的用户的连接。telnet协议不安全且未加密。 \n使用未加密的传输介质可以允许具有访问嗅探网络流量的用户窃取凭证的能力。 ssh包提供加密会话和更强的安全性。'


def _inetd_has_service(names):
    cfgs = ['/etc/inetd.conf']
    found = []
    for c in cfgs:
        if not os.path.exists(c):
            continue
        body = public.readFile(c) or ''
        for line in body.splitlines():
            s = line.strip()
            if not s or s.startswith('#'):
                continue
            for n in names:
                if s.startswith(n + ' '):
                    found.append(c + ':' + s)
    ddir = '/etc/inetd.d'
    if os.path.isdir(ddir):
        for name in os.listdir(ddir):
            fp = os.path.join(ddir, name)
            body = public.readFile(fp) or ''
            for line in body.splitlines():
                s = line.strip()
                if not s or s.startswith('#'):
                    continue
                for n in names:
                    if s.startswith(n + ' '):
                        found.append(fp + ':' + s)
    return found


def _xinetd_service_enabled(names):
    files = ['/etc/xinetd.conf']
    ddir = '/etc/xinetd.d'
    if os.path.isdir(ddir):
        for name in os.listdir(ddir):
            files.append(os.path.join(ddir, name))
    enabled = []
    for fp in files:
        if not os.path.exists(fp):
            continue
        body = public.readFile(fp) or ''
        for n in names:
            if re.search(r'^\s*service\s+' + re.escape(n) + r'\b', body, re.M):
                dism = re.search(r'^\s*disable\s*=\s*(\w+)\s*$', body, re.M)
                if dism and dism.group(1).lower() == 'yes':
                    continue
                enabled.append(fp)
    return enabled


def check_run():
    try:
        names = ['telnet']
        inetd = _inetd_has_service(names)
        xinetd = _xinetd_service_enabled(names)
        if inetd or xinetd:
            return False, '检测到telnet服务启用：{}'.format(','.join(inetd + xinetd))
        return True, '无风险'
    except:
        return True, '无风险'