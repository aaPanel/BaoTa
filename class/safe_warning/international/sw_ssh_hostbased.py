import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SSH的HostbasedAuthentication被禁用'
_version = 1.0
_ps = '是否禁用SSH HostbasedAuthentication'
_level = 2
_date = '2025-11-18'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_hostbased.pl")
_tips = [
    "编辑`/etc/ssh/sshd_config`文件将`HostbasedAuthentication`设置为：no",
    "并重启SSH服务",
]
_help = ''
_remind = 'hostbasedauthentication参数指定是否允许通过.rhosts或/etc/hosts.equiv用户的受信任主机进行身份验证，以及成功的公钥客户端主机身份验证。\n此选项仅适用于ssh协议版本2。'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        values = re.findall(r'^\s*(?!#)\s*HostbasedAuthentication\s+(\S+)', conf, re.M)
        if not values:
            return True, '无风险'
        val = values[-1].strip().lower()
        if val in ('yes', 'on', 'true'):
            return False, '未禁用HostbasedAuthentication'
        return True, '无风险'
    except:
        return True, '无风险'