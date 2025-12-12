import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = "确保用户'.netrc'文件不可全局或组访问"
_version = 1.0
_ps = "检查.netrc权限是否不可全局或组访问"
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_netrc_mode.pl")
_tips = [
    "查找并修复：find /home -type f -name .netrc -exec chmod 600 {} +",
    "修复root：chmod 600 /root/.netrc"
]
_help = ''
_remind = '虽然系统管理员可以为用户的.netrc文件建立安全权限，但用户可以轻松覆盖这些权限。\n.netrc文件可能包含可能用于攻击其他系统的未加密密码'


def check_run():
    try:
        pf = '/etc/passwd'
        body = public.readFile(pf)
        if not body:
            return True, '无风险'
        bad = []
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
                path = os.path.join(home, '.netrc')
                if os.path.isfile(path):
                    mode = os.stat(path).st_mode & 0o777
                    if mode != 0o600:
                        bad.append('{}:{}:{}'.format(name, path, format(mode, 'o')))
            except:
                pass
        if bad:
            return False, '存在不安全权限的.netrc文件：{}'.format('、'.join(bad))
        return True, '无风险'
    except:
        return True, '无风险'