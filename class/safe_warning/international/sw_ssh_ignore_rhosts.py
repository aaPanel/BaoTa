import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SSH的IgnoreRhosts已启用'
_version = 1.0
_ps = '检查是否启用SSH IgnoreRhosts'
_level = 1
_date = '2025-11-18'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_ignore_rhosts.pl")
_tips = [
    "编辑 `/etc/ssh/sshd_config`文件将`IgnoreRhosts`设置为：yes",
    "并重启SSH服务 systemctl restart sshd",
]
_help = ''
_remind = 'IgnoreRhosts参数指定.rhosts和.shosts文件不会在RhostsRSAAuthentication或HostbasedAuthentication中使用。\n设置此参数将强制用户在使用ssh进行身份验证时输入密码。'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        values = re.findall(r'^\s*(?!#)\s*IgnoreRhosts\s+(\S+)', conf, re.M)
        if not values:
            return True, '无风险'
        val = values[-1].strip().lower()
        if val in ('yes', 'on', 'true'):  # 已启用
            return True, '无风险'
        return False, '未启用IgnoreRhosts'
    except:
        return True, '无风险'