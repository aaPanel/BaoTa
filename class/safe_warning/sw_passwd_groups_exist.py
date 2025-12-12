import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保/etc/passwd 中的所有组在 /etc/group存在'
_version = 1.0
_ps = '检查passwd文件中是否存在未定义的GID'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_passwd_groups_exist.pl")
_tips = [
    "检测缺失GID：`comm -23 <(awk -F: '{print $4}' /etc/passwd | sort -n | uniq) <(awk -F: '{print $3}' /etc/group | sort -n | uniq)`",
    "为缺失组创建占位：`groupadd -g <GID> grp_<GID>`（按需调整组名）"
]
_help = ''
_remind = '随着时间的推移，系统管理错误和更改可能会导致在/etc/passwd中定义组，但不会在/etc/group中定义。\n在/etc/passwd文件中定义但未在/etc/group文件中定义的组对系统构成威胁 安全性，因为组权限未得到妥善管理。'


def check_run():
    try:
        pf = '/etc/passwd'
        gf = '/etc/group'
        p_body = public.readFile(pf)
        g_body = public.readFile(gf)
        if not p_body or not g_body:
            return True, '无风险'
        gids_p = set()
        for line in p_body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) >= 4:
                try:
                    gids_p.add(int(parts[3]))
                except:
                    pass
        gids_g = set()
        for line in g_body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) >= 3:
                try:
                    gids_g.add(int(parts[2]))
                except:
                    pass
        missing = [str(g) for g in sorted(gids_p - gids_g)]
        if missing:
            return False, '缺少group定义的GID：{}（来源：/etc/passwd 第4字段）'.format(','.join(missing))
        return True, '无风险'
    except:
        return True, '无风险'