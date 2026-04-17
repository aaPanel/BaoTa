import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保没有用户有.forward文件'
_version = 1.0
_ps = '检查是否存在.forward文件'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_forward.pl")
_tips = [
    "批量删除：find /home -type f -name .forward -exec rm -f {} +",
    "删除root：rm -f /root/.forward"
]
_help = ''
_remind = '防止敏感邮件被转发或执行意外命令造成数据外泄与风险，.forward文件指定用于转发用户邮件的电子邮件地址。使用.forward文件会带来安全风险，因为敏感数据可能会无意中转移到组织外部。'


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
                path = os.path.join(home, '.forward')
                if os.path.isfile(path):
                    hits.append('{}:{}'.format(name, path))
            except:
                pass
        if hits:
            return False, '存在.forward文件：{}'.format('、'.join(hits))
        return True, '无风险'
    except:
        return True, '无风险'