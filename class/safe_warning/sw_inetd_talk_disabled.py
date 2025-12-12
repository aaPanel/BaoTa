import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保talk服务未启用'
_version = 1.0
_ps = '检查是否禁用talk/ntalk'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_inetd_talk_disabled.pl")
_tips = [
    "在`/etc/inetd.conf`与`/etc/inetd.d/*`注释/删除以`talk`或`ntalk`开头的行",
    "在`/etc/xinetd.conf`与`/etc/xinetd.d/*`将`talk`/`ntalk`服务`disable = yes`",
    "示例：编辑`/etc/xinetd.d/talk`、`/etc/xinetd.d/ntalk`设置`disable = yes`"
]
_help = ''
_remind = '通话软件使用户可以通过终端会话跨系统发送和接收消息。 默认情况下安装了谈话客户端（允许发起谈话会话）。\n由于软件使用未加密的协议进行通信，因此存在安全风险。'


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
        names = ['talk', 'ntalk']
        inetd = _inetd_has_service(names)
        xinetd = _xinetd_service_enabled(names)
        if inetd or xinetd:
            return False, '检测到talk/ntalk服务启用：{}'.format(','.join(inetd + xinetd))
        return True, '无风险'
    except:
        return True, '无风险'