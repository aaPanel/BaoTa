import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保本地登录警告标语已配置正确'
_version = 1.0
_ps = '检查是否清理本地登录标语'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_local_login_banner.pl")
_tips = [
    "编辑`/etc/issue`删除`\\m`、`\\r`、`\\s`、`\\v`配置",
    "根据站点策略填充统一警告内容，例如：",
    "echo \"Authorized uses only. All activity may be monitored and reported.\" > /etc/issue",
]
_help = ''
_remind = '在警告信息中显示操作系统和补丁级别的信息会对试图针对特定系统漏洞攻击的攻击者提供详细的系统信息。'


def check_run():
    try:
        cfile = '/etc/issue'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        bad = set(re.findall(r'(\\[mrsv])', conf))
        if bad:
            return False, '本地登录标语包含系统信息变量：{}'.format(','.join(sorted(bad)))
        return True, '无风险'
    except:
        return True, '无风险'