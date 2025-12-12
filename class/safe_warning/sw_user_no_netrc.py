import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import public

_title = '确保没有用户有.netrc文件'
_version = 1.0
_ps = '检查是否存在.netrc文件'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_user_no_netrc.pl")
_tips = [
    "批量删除：find /home -type f -name .netrc -exec rm -f {} +",
    "删除root：rm -f /root/.netrc"
]
_help = ''
_remind = '.netrc文件包含用于通过FTP登录远程主机以进行文件传输的数据。.netrc文件存在严重的安全风险，因为它以未加密的形式存储密码。 \n即使禁用了FTP，用户帐户也可能从其他系统中带来了.netrc文件，这些文件可能会对这些系统造成风险。'


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
                path = os.path.join(home, '.netrc')
                if os.path.isfile(path):
                    hits.append('{}:{}'.format(name, path))
            except:
                pass
        if hits:
            return False, '存在.netrc文件：{}'.format('、'.join(hits))
        return True, '无风险'
    except:
        return True, '无风险'