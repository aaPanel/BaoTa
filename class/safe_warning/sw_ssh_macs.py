import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保只使用了已批准的MAC算法'
_version = 1.0
_ps = '检查是否仅启用核准的SSH MAC算法'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_macs.pl")
_tips = [
    "编辑 /etc/ssh/sshd_config 文件设置为以下参数并重启SSH服务：",
    "MACs hmac-sha2-512,hmac-sha2-256",
]
_help = ''
_remind = 'MD5和96位MAC算法被认为是弱的，并且已经证明可以提高ssh降级攻击的可利用性。\n此变量限制SSH在通信期间可以使用的MAC算法的类型。'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*MACs\s+(.+)$', conf, re.M)
        if not matches:
            return True, '无风险'
        line = matches[-1].split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]
        allowed = {'hmac-sha2-512', 'hmac-sha2-256'}
        extra = [v for v in vals if v not in allowed]
        if extra:
            return False, '存在非核准MAC算法：{}'.format(','.join(extra))
        return True, '无风险'
    except:
        return True, '无风险'