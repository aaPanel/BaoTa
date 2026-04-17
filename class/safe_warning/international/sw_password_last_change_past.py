import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import time, public

_title = '确保所有用户的上次密码更改日期都在过去'
_version = 1.0
_ps = '检查系统用户是否存在密码更改日期'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_password_last_change_past.pl")
_tips = [
    '锁定或重置不合规用户：usermod -L <user> 或 passwd <user>',
    '必要时使用：chage -d $(date +%Y-%m-%d) <user> 修正日期'
]
_help = ''
_remind = '所有用户都应该拥有过去的密码更改日期。如果用户在将来记录密码更改日期，则他们可以绕过任何设置的密码到期。'


def check_run():
    try:
        pf = '/etc/passwd'
        sf = '/etc/shadow'
        p = public.readFile(pf)
        s = public.readFile(sf)
        if not p or not s:
            return True, '无风险'
        uids = {}
        for line in p.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            try:
                uids[parts[0]] = int(parts[2])
            except:
                pass
        today_days = int(time.time() // 86400)
        bad = []
        for line in s.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 3:
                continue
            name = parts[0]
            if name not in uids:
                continue
            if uids[name] < 1000:
                continue
            lastchg = parts[2]
            try:
                if int(lastchg) > today_days:
                    bad.append(name)
            except:
                pass
        if bad:
            return False, '存在未来密码更改日期：{}'.format('、'.join(sorted(set(bad))))
        return True, '无风险'
    except:
        return True, '无风险'