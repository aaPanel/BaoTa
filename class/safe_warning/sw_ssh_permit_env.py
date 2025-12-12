import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SSH的PermitUserEnvironment被禁用'
_version = 1.0
_ps = '检查是否禁用SSH PermitUserEnvironment'
_level = 1
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_permit_env.pl")
_tips = [
    "编辑`/etc/ssh/sshd_config`文件将PermitUserEnvironment设置为no:",
    "PermitUserEnvironment no",
    "并重启SSH服务",
]
_help = ''
_remind = '允许用户通过ssh守护进程设置环境变量的能力可能会允许用户绕过安全控制（例如，设置具有ssh执行特洛伊木马程序的执行路径）'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*PermitUserEnvironment\s+(.+)$', conf, re.M)
        if not matches:
            return False, '未禁用PermitUserEnvironment'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v in ('yes', 'on', 'true'):
            return False, '未禁用PermitUserEnvironment'
        if v != 'no':
            return False, '未禁用PermitUserEnvironment'
        return True, '无风险'
    except:
        return True, '无风险'