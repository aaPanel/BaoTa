import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保只使用了已核准的密码'
_version = 1.0
_ps = '检查是否启用核准的SSH密码算法'
_level = 2
_date = '2025-11-18'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_ciphers.pl")
_tips = [
    "编辑` /etc/ssh/sshd_config` 文件设置以下参数并重启SSH服务：",
    "`Ciphers aes256-ctr,aes192-ctr,aes128-ctr`",
]
_help = ''
_remind = '此变量限制SSH在通信期间可以使用的密码类型，防止连接被降级与破解'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*Ciphers\s+(.+)$', conf, re.M)
        if not matches:
            return True, '无风险'
        line = matches[-1].strip()
        line = line.split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]
        allowed = {'aes256-ctr', 'aes192-ctr', 'aes128-ctr'}
        extra = [v for v in vals if v not in allowed]
        if extra:
            return False, '存在非核准密码算法：{}'.format(','.join(extra))
        return True, '无风险'
    except:
        return True, '无风险'