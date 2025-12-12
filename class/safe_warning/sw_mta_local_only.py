import sys, os
os.chdir('/www/server/panel')
sys.path.append("class/")
import re, public

_title = '确保邮件传输代理仅限本地模式'
_version = 1.0
_ps = '检查是否限制邮件传输代理配置仅本地'
_level = 2
_date = '2025-11-20'
_ignore = os.path.exists("data/warning/ignore/sw_mta_local_only.pl")
_tips = [
    "设置：postconf -e 'inet_interfaces = 127.0.0.1'",
    "重启：systemctl restart postfix"
]
_help = ''
_remind = '如果系统是邮件服务器，请忽略此检查项。\n建议将MTA配置为仅处理本地邮件，非邮件服务器将MTA限定为本地可显著降低暴露面与被利用风险。'


def check_run():
    try:
        cfile = '/etc/postfix/main.cf'
        if not os.path.exists(cfile):
            return True, '无风险'
        conf = public.readFile(cfile)
        if not conf:
            return True, '无风险'
        vals = re.findall(r'^\s*(?!#)\s*inet_interfaces\s*=\s*(\S+)', conf, re.M)
        if not vals:
            return False, '未在/etc/postfix/main.cf配置inet_interfaces=127.0.0.1'
        v = vals[-1].split('#')[0].strip().lower()
        if v != '127.0.0.1':
            return False, 'inet_interfaces未设置为127.0.0.1（/etc/postfix/main.cf）'
        return True, '无风险'
    except:
        return True, '无风险'