import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保没有用户有.rhosts文件'
_version = 1.0
_ps = '检查是否存在.rhosts文件'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_rhosts.pl")
_tips = [
    "查找并删除：`find /home -type f -name .rhosts -exec rm -f {} +`",
    "删除root家目录：`rm -f /root/.rhosts`"
]
_help = ''
_remind = '虽然默认情况下不会发送.rhosts文件，但用户可以轻松创建它们。 只有在/etc/pam.conf文件中允许.rhosts支持时，此操作才有意义。 \n即使.rhosts文件在/etc/pam.conf中禁用支持也无效，但它们可能已从其他系统引入，并且可能包含对其他系统的攻击者有用的信息。'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, '无风险'
        hits = []
        for line in body.splitlines():
            if not line or line.startswith('#'):
                continue
            parts = line.split(':')
            if len(parts) < 7:
                continue
            name, home = parts[0], parts[5]
            if not home or home == '/':
                continue
            try:
                rhosts_path = os.path.join(home, '.rhosts')
                if os.path.isfile(rhosts_path):
                    hits.append('{}:{}'.format(name, rhosts_path))
            except:
                pass
        if hits:
            return False, '检测到.rhosts：{}（共{}个）'.format('、'.join(hits), len(hits))
        return True, '无风险'
    except:
        return True, '无风险'