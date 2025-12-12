import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保rsh服务器未启用'
_version = 1.0
_ps = '检查是否禁用rsh/rlogin/rexec'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_rsh_disabled.pl")
_tips = [
    "在`/etc/inetd.conf`与`/etc/inetd.d/*`注释/删除以`shell`、`login`、`exec`开头的行",
    "在`/etc/xinetd.conf`与`/etc/xinetd.d/*`将`rsh`/`rlogin`/`rexec`服务`disable = yes`",
    "示例：编辑`/etc/xinetd.d/rsh`、`/etc/xinetd.d/rlogin`、`/etc/xinetd.d/rexec`设置`disable = yes`"
]
_help = ''
_remind = 'Berkeley rsh-server（rsh，rlogin，rexec）软件包包含以明文形式交换凭证的遗留服务。\n这些遗留服务包含大量安全风险，已被更安全的SSH软件包取代。'


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
            # rsh相关服务可能以service rsh/rlogin/rexec出现，也可能通过disable字段控制
            if re.search(r'^\s*service\s+' + re.escape(n) + r'\b', body, re.M):
                dism = re.search(r'^\s*disable\s*=\s*(\w+)\s*$', body, re.M)
                if dism and dism.group(1).lower() == 'yes':
                    continue
                enabled.append(fp)
    return enabled


def check_run():
    try:
        inetd_names = ['shell', 'login', 'exec']
        xinetd_names = ['rsh', 'rlogin', 'rexec']
        inetd = _inetd_has_service(inetd_names)
        xinetd = _xinetd_service_enabled(xinetd_names)
        if inetd or xinetd:
            return False, '检测到rsh相关服务启用：{}'.format(','.join(inetd + xinetd))
        return True, '无风险'
    except:
        return True, '无风险'