import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保使用强密钥交换算法'
_version = 1.0
_ps = '检查是否启用强密钥交换算法'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_kexalgorithms.pl")
_tips = [
    "编辑/etc/ssh/sshd_config文件添加/修改kexalgorithms行，以包含站点批准的强密钥交换算法的逗号分隔列表：",
    "KexAlgorithms curve25519-sha256,curve25519-sha256@libssh.org,diffie-hellman-group14-sha256,diffie-hellman-group16-sha512,diffie-hellman-group18-sha512,ecdh-sha2-nistp521,ecdh-sha2-nistp384,ecdh-sha2-nistp256,diffie-hellman-group-exchange-sha256",
    "重启 sshd : systemctl restart sshd",
]
_help = ''
_remind = '密钥交换是密码术中的任何方法，通过该方法在两方之间交换密码密钥，允许使用密码算法。 \n如果发送方和接收方希望交换加密消息，则必须配备每个加密消息以加密要发送的消息并解密接收的消息'


def check_run():
    try:
        # 仅centos系统检测
        if not os.path.exists('/etc/centos-release'):
            return True, '无风险'

        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*KexAlgorithms\s+(.+)$', conf, re.M)
        if not matches:
            return True, '无风险'
        line = matches[-1].split('#')[0].strip()
        vals = [v.strip().lower() for v in line.replace('"', '').replace("'", '').split(',') if v.strip()]
        allowed = {
            'curve25519-sha256',
            'curve25519-sha256@libssh.org',
            'diffie-hellman-group14-sha256',
            'diffie-hellman-group16-sha512',
            'diffie-hellman-group18-sha512',
            'ecdh-sha2-nistp521',
            'ecdh-sha2-nistp384',
            'ecdh-sha2-nistp256',
            'diffie-hellman-group-exchange-sha256',
        }
        extra = [v for v in vals if v not in allowed]
        if extra:
            return False, '存在非核准密钥交换算法：{}'.format(','.join(extra))
        return True, '无风险'
    except:
        return True, '无风险'