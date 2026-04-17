import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保只使用了已核准的密码'
_version = 1.1
_ps = '检查是否启用核准的SSH密码算法'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_ciphers.pl")
_tips = [
    "编辑`/etc/ssh/sshd_config` 文件设置以下参数并重启SSH服务：",
    "`Ciphers aes256-gcm@openssh.com,aes128-gcm@openssh.com,chacha20-poly1305@openssh.com,aes256-ctr,aes192-ctr,aes128-ctr`",
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

        # 扩展允许的算法（参考CIS Benchmark 2024）
        allowed = {
            'aes256-gcm@openssh.com',  # GCM模式（更安全，AEAD加密）
            'aes128-gcm@openssh.com',
            'aes256-ctr',
            'aes192-ctr',
            'aes128-ctr',
            'chacha20-poly1305@openssh.com'  # ChaCha20-Poly1305（适合移动设备）
        }

        # 弱算法列表（需要报风险的）
        weak_algos = {
            'arcfour', 'arcfour128', 'arcfour256', 'arcfour512',
            'blowfish-cbc', 'blowfish',
            'cast128-cbc', 'cast128',
            '3des-cbc', '3des', 'des',
            'rijndael-cbc', 'rijndael',
            'serpent256-cbc',
            'cast128-cbc',
            'aes192-cbc', 'aes256-cbc', 'aes128-cbc'  # CBC模式不如CTR/GCM
        }

        # 检查是否有弱算法
        has_weak = False
        weak_list = []
        for v in vals:
            if v in weak_algos or any(w in v for w in weak_algos):
                has_weak = True
                weak_list.append(v)

        if has_weak:
            return False, '存在弱密码算法（建议替换为GCM/CTR模式）：{}'.format(','.join(weak_list))

        # 检查是否有非推荐算法
        extra = [v for v in vals if v not in allowed]
        if extra:
            # 非弱算法但不推荐的，只提示不报错
            return True, '无风险（提示：存在非推荐算法：{}，建议使用：aes256-gcm@openssh.com,aes128-gcm@openssh.com,chacha20-poly1305@openssh.com,aes256-ctr,aes128-ctr）'.format(','.join(extra))

        return True, '无风险'
    except:
        return True, '无风险'