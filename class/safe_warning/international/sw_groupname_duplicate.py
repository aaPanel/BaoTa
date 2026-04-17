import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保重复用户组名称不存在'
_version = 1.0
_ps = '检查用户组内是否存在重复组名'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_groupname_duplicate.pl")
_tips = [
    "检测重复组名：awk -F: '{print $1}' /etc/group | sort | uniq -d",
    "重命名组：groupmod -n <新组名> <旧组名>"
]
_help = ''
_remind = '防止重复组名导致访问与审计混乱。'


def check_run():
    try:
        gf = '/etc/group'
        body = public.readFile(gf)
        if not body:
            return True, '无风险'
        names = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 3:
                continue
            name = parts[0]
            names[name] = names.get(name, 0) + 1
        dup = [n for n, c in names.items() if c > 1]
        if dup:
            return False, '存在重复组名：{}'.format(','.join(dup))
        return True, '无风险'
    except:
        return True, '无风险'