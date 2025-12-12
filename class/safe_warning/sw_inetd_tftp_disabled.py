import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保tftp服务未启用'
_version = 1.0
_ps = '检查是否禁用tftp服务'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_tftp_disabled.pl")
_tips = [
    "在`/etc/inetd.conf`与`/etc/inetd.d/*`注释/删除以`tftp`开头的行",
    "在`/etc/xinetd.conf`与`/etc/xinetd.d/*`中将`tftp`服务`disable = yes`"
]
_help = ''
_remind = 'TFTP不支持身份验证，不确保数据的机密性或完整性。建议禁用TFTP，除非有特殊需要。\n在这种情况下，配置服务时必须格外小心。'


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
        names = ['tftp']
        inetd = _inetd_has_service(names)
        xinetd = _xinetd_service_enabled(names)
        if inetd or xinetd:
            return False, '检测到tftp服务启用：{}'.format(','.join(inetd + xinetd))
        return True, '无风险'
    except:
        return True, '无风险'