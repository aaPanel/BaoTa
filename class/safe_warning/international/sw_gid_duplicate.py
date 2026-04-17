import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保重复GID不存在'
_version = 1.0
_ps = '检查用户组是否存在重复GID'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_gid_duplicate.pl")
_tips = [
    "检测重复GID：`awk -F: '{print $3}' /etc/group | sort | uniq -d`",
    "列出共享GID的组：`awk -F: 'NR==FNR{a[$3]++;next} a[$3]>1{print $1\":\"$3}' /etc/group /etc/group`",
    "修复示例：`groupmod -g <新GID> <组名>`，并迁移文件：`find / -group <旧GID> -exec chgrp <组名> {} +`",
    "第二种：点击【系统加固】-【等保加固】-【访问控制】，查看用户审计，针对风险描述，进行调整用户组ID"
]
_help = ''
_remind = '重复GID会导致访问控制与审计混乱；修复后可确保权限边界与责任归属清晰'


def check_run():
    try:
        gf = '/etc/group'
        body = public.readFile(gf)
        if not body:
            return True, '无风险'
        gid_map = {}
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 3:
                continue
            name, gid = parts[0], parts[2]
            try:
                k = int(gid)
            except:
                continue
            gid_map.setdefault(k, []).append(name)
        dup = ['{}:{}'.format(k, ','.join(v)) for k, v in gid_map.items() if len(v) > 1]
        if dup:
            return False, '存在重复GID：{}'.format('；'.join(dup))
        return True, '无风险'
    except:
        return True, '无风险'