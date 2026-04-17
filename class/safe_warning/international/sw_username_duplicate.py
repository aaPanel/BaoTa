import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保重复用户名不存在'
_version = 1.0
_ps = '检查是否重复用户名'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_username_duplicate.pl")
_tips = [
    "检测重复用户名：`awk -F: '{print $1}' /etc/passwd | sort | uniq -d`",
    "修复示例：`usermod -l <新用户名> <旧用户名>`"
]
_help = ''
_remind = '虽然默认情况下不会发送.rhosts文件，但用户可以轻松创建它们。 只有在/etc/pam.conf文件中允许.rhosts支持时，此操作才有意义。 \n即使.rhosts文件在/etc/pam.conf中禁用支持也无效，但它们可能已从其他系统引入，并且可能包含对其他系统的攻击者有用的信息。'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, '无风险'
        names = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name = parts[0]
            names[name] = names.get(name, 0) + 1
        dup = [n for n, c in names.items() if c > 1]
        if dup:
            return False, '存在重复用户名：{}'.format(','.join(dup))
        return True, '无风险'
    except:
        return True, '无风险'