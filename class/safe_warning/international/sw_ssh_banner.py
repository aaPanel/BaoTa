import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保SSH警告通知已设置'
_version = 1.1
_ps = '检查是否设置SSH登录警告'
_level = 2
_date = '2025-01-15'
_ignore = os.path.exists("data/warning/ignore/sw_ssh_banner.pl")
_tips = [
    "编辑`/etc/ssh/sshd_config`文件设置Banner路径并重启SSH服务：",
    "Banner /etc/issue.net 或 /etc/issue 或其他自定义路径",
]
_help = ''
_remind = 'Banner参数指定在允许身份验证之前必须将其内容发送给远程用户的文件。\n在正常用户登录之前显示警告消息可能有助于警告计算机系统上的侵入者。'


def check_run():
    try:
        cfile = '/etc/ssh/sshd_config'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        matches = re.findall(r'^\s*(?!#)\s*Banner\s+(.+)$', conf, re.M)
        if not matches:
            return False, '未设置Banner或被置为none'
        val = matches[-1].split('#')[0].strip().strip('"').strip("'")
        v = val.lower()
        if v in ('none', ''):
            return False, '未设置SSH警告通知'

        # 改为：只要设置了Banner且文件存在即可，不限制具体路径
        if os.path.exists(val):
            return True, '无风险'
        else:
            return False, 'Banner文件不存在：{}'.format(val)
    except:
        return True, '无风险'