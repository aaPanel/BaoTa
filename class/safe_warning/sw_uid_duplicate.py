import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保重复UID不存在'
_version = 1.0
_ps = '检查是否存在重复UID'
_level = 3
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_uid_duplicate.pl")
_tips = [
    "点击【系统加固】插件，进入等保加固-访问控制-用户审计，检查重复UID的用户，若不需要该重复UID用户，可删除",
]
_help = ''
_remind = '尽管useradd程序不允许您创建重复的用户ID（UID），但管理员可以手动编辑/etc/passwd文件并更改UID字段。\n必须为用户分配唯一的UID以确保问责制并确保适当的访问保护。'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, '无风险'
        uid_map = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name, uid = parts[0], parts[2]
            try:
                k = int(uid)
            except:
                continue
            uid_map.setdefault(k, []).append(name)
        dup = ['{}:{}'.format(k, ','.join(v)) for k, v in uid_map.items() if len(v) > 1]
        if dup:
            return False, '存在重复UID：{}'.format('；'.join(dup))
        return True, '无风险'
    except:
        return True, '无风险'